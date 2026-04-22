from fastapi import APIRouter
from typing import List, Optional

from app.schemas.tournament import MatchCreate, MatchResponse, MatchUpdate

router = APIRouter(tags=["Tournament Matches"]) 

# Пока демонстрационные данные (без БД)
DEMO_MATCHES: List[dict] = [
    {
        "id": 1,
        "team1_name": "Carnivorous",
        "team2_name": "Carnivorous",
        "team1_score": 0,
        "team2_score": 3,
        "stage": "playoffs",
        "round_number": 1,
        "logs_url": "+",
    },
    {
        "id": 2,
        "team1_name": "Carnivorous",
        "team2_name": "Carnivorous",
        "team1_score": 0,
        "team2_score": 3,
        "stage": "group_stage",
        "round_number": 2,
        "logs_url": "-",
    },
]


def stage_filter_to_key(stage_filter: Optional[str]) -> str:
    if not stage_filter:
        return "ALL"
    s = stage_filter.strip().upper()
    if s == "GROUP STAGE":
        return "group_stage"
    if s == "PLAYOFFS":
        return "playoffs"
    if s == "FINALS":
        return "finals"
    return "ALL"


@router.get("/tournaments/{tournament_id}/matches", response_model=List[MatchResponse])
async def get_tournament_matches(
    tournament_id: int,
    search: Optional[str] = None,
    stage: Optional[str] = None,
    round: Optional[int] = None,
):
    # tournament_id пока не используется (демо)
    q = (search or '').strip().lower()
    stage_key = stage_filter_to_key(stage)

    def matches_filters(m: dict) -> bool:
        name = f"{m.get('team1_name','')} {m.get('team2_name','')}".lower()
        match_search = (not q) or (q in name)
        match_stage = (stage_key == 'ALL') or (str(m.get('stage','')).lower() == stage_key)
        match_round = (round is None) or (int(m.get('round_number')) == round)
        return match_search and match_stage and match_round

    return [MatchResponse(**m) for m in DEMO_MATCHES if matches_filters(m)]


@router.post("/tournaments/{tournament_id}/matches", response_model=MatchResponse, status_code=201)
async def create_tournament_match(
    tournament_id: int,
    body: MatchCreate,
):
    # Без БД: просто возвращаем данные как будто создано.
    created = body.model_dump()
    created["id"] = created.get("id") or 1
    created["tournament_id"] = tournament_id
    return MatchResponse(**created)


@router.patch("/tournaments/{tournament_id}/matches/{match_id}", response_model=MatchResponse)
async def update_tournament_match(
    tournament_id: int,
    match_id: int,
    body: MatchUpdate,
):
    update_data = body.model_dump(exclude_unset=True)
    # Без БД: возвращаем match_id и обновлённые поля.
    return MatchResponse(
        id=match_id,
        tournament_id=tournament_id,
        team1_name=update_data.get("team1_name", "Carnivorous"),
        team2_name=update_data.get("team2_name", "Carnivorous"),
        team1_score=update_data.get("team1_score", 0),
        team2_score=update_data.get("team2_score", 3),
        stage=update_data.get("stage", "playoffs"),
        round_number=update_data.get("round_number", 1),
        logs_url=update_data.get("logs_url", "-"),
    )
