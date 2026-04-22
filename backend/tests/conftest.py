"""
Conftest для тестов MoonRise.
Содержит общие фикстуры и утилиты.
"""
import sys
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone


# ============================================================
# МОКИ ДЛЯ БД (чтобы не требовался asyncpg)
# ============================================================

# Мокаем asyncpg до импорта любых модулей БД
mock_asyncpg = MagicMock()
sys.modules['asyncpg'] = mock_asyncpg


class MockDBSession:
    """Мокированная сессия базы данных для тестов."""

    def __init__(self):
        self.add = MagicMock()
        self.flush = AsyncMock()
        self.commit = AsyncMock()
        self.refresh = AsyncMock()
        self.execute = AsyncMock()
        self.delete = AsyncMock()
        self.scalars = MagicMock()
        self.query = MagicMock()

    async def mock_execute(self, query):
        """Мокирует execute для возврата результатов."""
        return self.execute.return_value


@pytest.fixture
def mock_db():
    """Создает мокированную сессию БД."""
    return MockDBSession()


@pytest.fixture
def mock_tournament():
    """Создает мок турнира."""
    tournament = MagicMock()
    tournament.id = 1
    tournament.title = "Test Tournament"
    tournament.format = "mix"
    tournament.status = "ongoing"
    return tournament


@pytest.fixture
def mock_stage_group_a():
    """Создает мок группы A."""
    group = MagicMock()
    group.id = 1
    group.name = "Группа A"
    group.stage_id = 1
    return group


@pytest.fixture
def mock_stage_group_b():
    """Создает мок группы B."""
    group = MagicMock()
    group.id = 2
    group.name = "Группа B"
    group.stage_id = 1
    return group


@pytest.fixture
def mock_participants_group_a():
    """Создает моки участников группы A."""
    participants = []
    for i in range(1, 6):
        p = MagicMock()
        p.id = i
        p.user_id = 100 + i
        p.tournament_id = 1
        p.group_id = 1
        p.seed = i
        p.status = "registered"
        p.is_allowed = True
        participants.append(p)
    return participants


@pytest.fixture
def mock_participants_group_b():
    """Создает моки участников группы B."""
    participants = []
    for i in range(1, 5):
        p = MagicMock()
        p.id = 10 + i
        p.user_id = 200 + i
        p.tournament_id = 1
        p.group_id = 2
        p.seed = i
        p.status = "registered"
        p.is_allowed = True
        participants.append(p)
    return participants


@pytest.fixture
def mock_teams():
    """Создает моки команд."""
    teams = []
    for i in range(1, 11):
        team = MagicMock()
        team.id = i
        team.name = f"Team {i}"
        team.tournament_id = 1
        team.captain_user_id = 100 + i
        teams.append(team)
    return teams


@pytest.fixture
def mock_encounters():
    """Создает моки встреч."""
    encounters = []
    for i in range(1, 6):
        enc = MagicMock()
        enc.id = i
        enc.tournament_id = 1
        enc.stage_id = 1
        enc.team1_id = i * 2 - 1
        enc.team2_id = i * 2
        enc.team1_score = 0
        enc.team2_score = 0
        enc.winner_team_id = None
        enc.stage = "Test Stage"
        enc.round_number = 1
        enc.is_auto_created = 1
        encounters.append(enc)
    return encounters
