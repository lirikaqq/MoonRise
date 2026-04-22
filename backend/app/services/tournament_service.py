from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import selectinload, joinedload
from app.models.tournament import Tournament, TournamentParticipant
from app.models.player_replacement import PlayerReplacement
from app.models.match import Team, Encounter
from app.models.user import User
from app.schemas.tournament import (
    TournamentCreate, 
    TournamentUpdate, 
    ReplacePlayerRequest, 
    ReplacementResponse, 
    TeamWithHistoryResponse
)
from fastapi import HTTPException
from typing import Optional, Dict, List
import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class TeamConfigImmutableError(HTTPException):
    """Выбрасывается при попытке изменить team_config после начала турнира."""
    def __init__(self, detail: str = "team_config is immutable: teams, draft_session or encounters already exist"):
        super().__init__(status_code=409, detail=detail)


class TournamentService:
    """Сервис для работы с турнирами."""

    @staticmethod
    async def assert_can_modify_team_config(tournament: Tournament, db: AsyncSession) -> None:
        """Центральная проверка иммутабельности team_config."""
        await db.execute(
            select(Tournament)
            .options(
                selectinload(Tournament.teams),
                selectinload(Tournament.draft_session),
                selectinload(Tournament.encounters),
            )
            .where(Tournament.id == tournament.id)
        )
        await db.refresh(tournament)

        if tournament.teams and len(tournament.teams) > 0:
            raise TeamConfigImmutableError("Cannot modify team_config: teams already exist")

        if tournament.draft_session is not None:
            raise TeamConfigImmutableError("Cannot modify team_config: draft session already started")

        if tournament.encounters and len(tournament.encounters) > 0:
            raise TeamConfigImmutableError("Cannot modify team_config: encounters already exist")

        logger.info(f"team_config modification allowed for tournament {tournament.id}")

    @staticmethod
    async def get_by_id(
        db: AsyncSession, 
        tournament_id: int, 
        load_relations: bool = False
    ) -> Tournament:
        query = select(Tournament)
        if load_relations:
            query = query.options(
                selectinload(Tournament.teams),
                selectinload(Tournament.draft_session),
                selectinload(Tournament.encounters),
            )

        result = await db.execute(query.where(Tournament.id == tournament_id))
        tournament = result.scalar_one_or_none()

        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")
        return tournament

    @staticmethod
    async def update(
        db: AsyncSession,
        tournament_id: int,
        data: TournamentUpdate
    ) -> Tournament:
        """Обновление турнира с защитой team_config."""
        tournament = await TournamentService.get_by_id(db, tournament_id, load_relations=True)

        update_data = data.model_dump(exclude_unset=True)

        if "team_config" in update_data and update_data.get("team_config") is not None:
            await TournamentService.assert_can_modify_team_config(tournament, db)

        for field, value in update_data.items():
            if value is not None:
                setattr(tournament, field, value)

        await db.commit()
        await db.refresh(tournament)
        return tournament

    @staticmethod
    async def delete_tournament(db: AsyncSession, tournament_id: int) -> Optional[Tournament]:
        """Удаляет турнир и все связанные с ним данные (hard delete)."""
        tournament = await TournamentService.get_by_id(db, tournament_id)
        await db.delete(tournament)
        await db.commit()
        return tournament

    @staticmethod
    async def update_status(
        db: AsyncSession,
        tournament_id: int,
        status: str
    ) -> Tournament:
        """Изменить статус турнира."""
        valid_statuses = ["upcoming", "registration", "checkin", "draft", "ongoing", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )

        tournament = await TournamentService.get_by_id(db, tournament_id)
        tournament.status = status
        await db.commit()
        await db.refresh(tournament)
        return tournament

    @staticmethod
    async def get_bracket(db: AsyncSession, tournament_id: int) -> dict:
        """Собирает все матчи турнира и возвращает JSON сетки."""
        await TournamentService.get_by_id(db, tournament_id)

        query = (
            select(Encounter)
            .options(
                joinedload(Encounter.team1),
                joinedload(Encounter.team2)
            )
            .where(Encounter.tournament_id == tournament_id)
            .order_by(Encounter.round_number.asc(), Encounter.id.asc())
        )
        
        result = await db.execute(query)
        encounters = result.scalars().all()

        if not encounters:
            return {"upper_bracket": []}

        rounds_map = defaultdict(list)
        for enc in encounters:
            r_num = enc.round_number or 1
            rounds_map[r_num].append(enc)

        upper_bracket = []
        sorted_rounds = sorted(rounds_map.keys())
        
        for r_num in sorted_rounds:
            matches = []
            for enc in rounds_map[r_num]:
                t1_is_winner = (enc.winner_team_id == enc.team1_id) if enc.winner_team_id else False
                t2_is_winner = (enc.winner_team_id == enc.team2_id) if enc.winner_team_id else False
                
                matches.append({
                    "id": enc.id,
                    "isEmpty": False,
                    "team1": {
                        "name": enc.team1.name if enc.team1 else "TBD",
                        "score": enc.team1_score,
                        "isWinner": t1_is_winner
                    },
                    "team2": {
                        "name": enc.team2.name if enc.team2 else "TBD",
                        "score": enc.team2_score,
                        "isWinner": t2_is_winner
                    }
                })
            
            upper_bracket.append({
                "round_name": f"ROUND {r_num}",
                "matches": matches
            })

        if len(upper_bracket) > 1:
            upper_bracket[-1]["round_name"] = "GRAND FINAL"
        if len(upper_bracket) > 2:
            upper_bracket[-2]["round_name"] = "SEMI-FINAL"

        return {"upper_bracket": upper_bracket}

    @staticmethod
    async def set_captain_status(
        db: AsyncSession,
        participant_id: int,
        is_captain: bool
    ) -> TournamentParticipant:
        result = await db.execute(
            select(TournamentParticipant).where(TournamentParticipant.id == participant_id)
        )
        participant = result.scalar_one_or_none()

        if not participant:
            raise HTTPException(status_code=404, detail="Tournament participant not found")

        participant.is_captain = is_captain
        await db.commit()
        await db.refresh(participant)
        return participant

    @staticmethod
    async def get_tournament_captains(
        db: AsyncSession,
        tournament_id: int
    ) -> list[TournamentParticipant]:
        result = await db.execute(
            select(TournamentParticipant)
            .options(joinedload(TournamentParticipant.user))
            .where(
                and_(
                    TournamentParticipant.tournament_id == tournament_id,
                    TournamentParticipant.is_captain == True
                )
            )
            .order_by(TournamentParticipant.registered_at)
        )
        return result.scalars().all()

    # ====================== СИСТЕМА ЗАМЕНЫ ИГРОКОВ ======================

    @staticmethod
    async def replace_player(
        db: AsyncSession,
        tournament_id: int,
        team_id: int,
        old_participant_id: int,
        new_participant_id: int,
        replaced_by_user_id: int,
        reason: Optional[str] = None,
    ) -> Dict:
        """
        Заменяет игрока в команде турнира.
        Только для админа.
        """
        tournament = await TournamentService.get_by_id(db, tournament_id, load_relations=True)

        result = await db.execute(
            select(TournamentParticipant)
            .where(TournamentParticipant.id.in_([old_participant_id, new_participant_id]))
        )
        participants = {p.id: p for p in result.scalars().all()}

        old_p = participants.get(old_participant_id)
        new_p = participants.get(new_participant_id)

        if not old_p or not new_p:
            raise HTTPException(status_code=404, detail="One or both participants not found")

        if old_p.team_id != team_id:
            raise HTTPException(status_code=400, detail="Old participant does not belong to this team")

        if new_p.team_id is not None and new_p.team_id != team_id:
            raise HTTPException(status_code=400, detail="New participant is already in another team")

        if not old_p.is_active:
            raise HTTPException(status_code=400, detail="Old participant is not active")

        # Создаём запись о замене
        replacement = PlayerReplacement(
            tournament_id=tournament_id,
            team_id=team_id,
            old_participant_id=old_participant_id,
            new_participant_id=new_participant_id,
            replaced_by_user_id=replaced_by_user_id,
            reason=reason,
            previous_is_captain=old_p.is_captain,
        )

        db.add(replacement)

        # Обновляем участников
        old_p.is_active = False
        new_p.is_active = True
        new_p.team_id = team_id

        # Если заменяли капитана — передаём статус
        if old_p.is_captain:
            old_p.is_captain = False
            new_p.is_captain = True

        await db.commit()
        await db.refresh(replacement)
        await db.refresh(old_p)
        await db.refresh(new_p)

        logger.info(f"Player replaced in tournament {tournament_id}, team {team_id}: "
                   f"{old_participant_id} → {new_participant_id} by user {replaced_by_user_id}")

        return {
            "success": True,
            "replacement": ReplacementResponse.model_validate(replacement),
            "old_participant": {"id": old_p.id, "username": old_p.user.username if old_p.user else None},
            "new_participant": {"id": new_p.id, "username": new_p.user.username if new_p.user else None},
        }


    @staticmethod
    async def undo_replace(
        db: AsyncSession,
        replacement_id: int,
        undone_by_user_id: int
    ) -> Dict:
        """
        Откатывает замену игрока.
        """
        result = await db.execute(
            select(PlayerReplacement)
            .options(
                joinedload(PlayerReplacement.old_participant),
                joinedload(PlayerReplacement.new_participant)
            )
            .where(PlayerReplacement.id == replacement_id)
        )
        replacement = result.scalar_one_or_none()

        if not replacement:
            raise HTTPException(status_code=404, detail="Replacement record not found")

        # Восстанавливаем старого участника
        replacement.old_participant.is_active = True
        replacement.new_participant.is_active = False
        replacement.new_participant.team_id = None

        if replacement.previous_is_captain:
            replacement.old_participant.is_captain = True
            replacement.new_participant.is_captain = False

        await db.delete(replacement)
        await db.commit()

        logger.info(f"Replacement {replacement_id} undone by user {undone_by_user_id}")

        return {
            "success": True,
            "message": "Replacement successfully undone",
            "restored_participant_id": replacement.old_participant_id
        }


    @staticmethod
    async def get_team_with_history(
        db: AsyncSession,
        team_id: int
    ) -> Dict:
        """
        Возвращает состав команды + историю замен.
        """
        result = await db.execute(
            select(Team)
            .options(
                selectinload(Team.tournament_participants.and_(TournamentParticipant.is_active == True)),
                selectinload(Team.tournament_participants.and_(TournamentParticipant.is_active == False))
            )
            .where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        replacements_result = await db.execute(
            select(PlayerReplacement)
            .options(
                joinedload(PlayerReplacement.old_participant),
                joinedload(PlayerReplacement.new_participant),
                joinedload(PlayerReplacement.replaced_by_user)
            )
            .where(PlayerReplacement.team_id == team_id)
            .order_by(PlayerReplacement.replaced_at.desc())
        )

        return {
            "team": team,
            "active_participants": [p for p in team.tournament_participants if p.is_active],
            "replacement_history": [
                ReplacementResponse.model_validate(r) for r in replacements_result.scalars().all()
            ]
        }