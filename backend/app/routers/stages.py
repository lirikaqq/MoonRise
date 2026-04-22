"""
API endpoints для управления этапами и группами турнира.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

from app.database import get_db
from app.models.tournament_stage import TournamentStage, StageGroup, StageFormat, SeedingRule
from app.models.tournament import Tournament
from app.models.match import Encounter, Team
from app.schemas.stage import (
    TournamentStageCreate,
    TournamentStageUpdate,
    TournamentStageResponse,
    StageGroupCreate,
    StageGroupUpdate,
    StageGroupResponse,
    StageAdvancementResult
)
from app.services.stage_service import StageService

router = APIRouter(prefix="/api/stages", tags=["stages"])


# ============================================================
# ENDPOINTS ДЛЯ ЭТАПОВ (STAGES)
# ============================================================

@router.post("/", response_model=TournamentStageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(
    stage_data: TournamentStageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый этап для турнира."""
    # Проверяем, существует ли турнир
    tournament_result = await db.execute(
        select(Tournament).where(Tournament.id == stage_data.tournament_id)
    )
    tournament = tournament_result.scalar_one_or_none()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    stage = TournamentStage(
        tournament_id=stage_data.tournament_id,
        stage_number=stage_data.stage_number,
        name=stage_data.name,
        format=stage_data.format,
        settings=stage_data.settings.model_dump() if stage_data.settings else None
    )
    db.add(stage)
    await db.commit()

    # Перезагружаем с eager-loaded groups чтобы избежать ResponseValidationError
    result = await db.execute(
        select(TournamentStage)
        .options(joinedload(TournamentStage.groups))
        .where(TournamentStage.id == stage.id)
    )
    stage = result.unique().scalar_one_or_none()

    return stage


@router.get("/tournament/{tournament_id}", response_model=List[TournamentStageResponse])
async def get_tournament_stages(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить все этапы турнира."""
    result = await db.execute(
        select(TournamentStage)
        .options(joinedload(TournamentStage.groups))
        .where(TournamentStage.tournament_id == tournament_id)
        .order_by(TournamentStage.stage_number)
    )
    stages = result.unique().scalars().all()
    return stages


@router.get("/{stage_id}", response_model=TournamentStageResponse)
async def get_stage(
    stage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить детали этапа."""
    result = await db.execute(
        select(TournamentStage)
        .options(joinedload(TournamentStage.groups))
        .where(TournamentStage.id == stage_id)
    )
    stage = result.unique().scalar_one_or_none()

    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    return stage


@router.put("/{stage_id}", response_model=TournamentStageResponse)
async def update_stage(
    stage_id: int,
    stage_data: TournamentStageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить настройки этапа."""
    result = await db.execute(
        select(TournamentStage).where(TournamentStage.id == stage_id)
    )
    stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    update_data = stage_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "settings" and value is not None:
            setattr(stage, field, value.model_dump())
        else:
            setattr(stage, field, value)

    await db.commit()

    # Перезагружаем с eager-loaded groups
    result = await db.execute(
        select(TournamentStage)
        .options(joinedload(TournamentStage.groups))
        .where(TournamentStage.id == stage.id)
    )
    stage = result.unique().scalar_one_or_none()

    return stage


@router.delete("/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить этап."""
    result = await db.execute(
        select(TournamentStage).where(TournamentStage.id == stage_id)
    )
    stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    await db.delete(stage)
    await db.commit()


@router.post("/{stage_id}/generate-matches", response_model=List[dict])
async def generate_stage_matches(
    stage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Сгенерировать матчи для этапа на основе его формата.
    - ROUND_ROBIN: каждый с каждым внутри группы
    - SWISS: швейцарская система
    - SINGLE_ELIMINATION: одиночная сетка
    - DOUBLE_ELIMINATION: двойная сетка
    """
    encounters = await StageService.generate_stage_matches(db, stage_id)

    return [
        {
            "id": enc.id,
            "tournament_id": enc.tournament_id,
            "stage_id": enc.stage_id,
            "team1_id": enc.team1_id,
            "team2_id": enc.team2_id,
            "stage": enc.stage,
            "round_number": enc.round_number,
        }
        for enc in encounters
    ]


@router.post("/{stage_id}/advance", response_model=StageAdvancementResult)
async def advance_to_next_stage(
    stage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Продвинуть участников с текущего этапа на следующий.
    Применяет advancement_config из настроек этапа.
    """
    result = await StageService.advance_to_next_stage(db, stage_id)
    return result


# ============================================================
# ENDPOINTS ДЛЯ ГРУПП (GROUPS)
# ============================================================

@router.post("/{stage_id}/groups", response_model=StageGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    stage_id: int,
    group_data: StageGroupCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новую группу в этапе."""
    # Проверяем, существует ли этап
    stage_result = await db.execute(
        select(TournamentStage).where(TournamentStage.id == stage_id)
    )
    stage = stage_result.scalar_one_or_none()

    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    group = StageGroup(
        stage_id=stage_id,
        name=group_data.name
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    return group


@router.get("/{stage_id}/groups", response_model=List[StageGroupResponse])
async def get_stage_groups(
    stage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить все группы этапа."""
    result = await db.execute(
        select(StageGroup)
        .where(StageGroup.stage_id == stage_id)
        .order_by(StageGroup.name)
    )
    groups = result.scalars().all()
    return groups


@router.put("/groups/{group_id}", response_model=StageGroupResponse)
async def update_group(
    group_id: int,
    group_data: StageGroupUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить название группы."""
    result = await db.execute(
        select(StageGroup).where(StageGroup.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group_data.name:
        group.name = group_data.name

    await db.commit()
    await db.refresh(group)

    return group


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить группу."""
    result = await db.execute(
        select(StageGroup).where(StageGroup.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await db.delete(group)
    await db.commit()


# ============================================================
# ENDPOINTS ДЛЯ УПРАВЛЕНИЯ УЧАСТНИКАМИ В ГРУППАХ
# ============================================================

@router.post("/groups/{group_id}/participants/{participant_id}")
async def assign_participant_to_group(
    group_id: int,
    participant_id: int,
    seed: int = None,
    db: AsyncSession = Depends(get_db)
):
    """Назначить участника в группу с указанием seed."""
    from app.models.tournament import TournamentParticipant

    # Проверяем группу
    group_result = await db.execute(
        select(StageGroup).where(StageGroup.id == group_id)
    )
    group = group_result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Проверяем участника
    participant_result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.id == participant_id)
    )
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Назначаем
    participant.group_id = group_id
    if seed is not None:
        participant.seed = seed

    await db.commit()

    return {"message": "Participant assigned to group", "participant_id": participant_id, "group_id": group_id, "seed": seed}


@router.post("/groups/{group_id}/participants/bulk")
async def bulk_assign_participants(
    group_id: int,
    participant_ids: List[int],
    start_seed: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """Массовое назначение участников в группу."""
    from app.models.tournament import TournamentParticipant

    # Проверяем группу
    group_result = await db.execute(
        select(StageGroup).where(StageGroup.id == group_id)
    )
    group = group_result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Получаем всех участников
    participants_result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.id.in_(participant_ids))
    )
    participants = participants_result.scalars().all()

    # Назначаем
    for idx, participant in enumerate(participants):
        participant.group_id = group_id
        participant.seed = start_seed + idx

    await db.commit()

    return {"message": f"Assigned {len(participants)} participants to group", "group_id": group_id}
