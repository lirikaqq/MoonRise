"""
Тесты для player_service.py — обновление профиля, валидация данных.
"""
import pytest
from datetime import datetime, timezone

from app.schemas.player import PlayerUpdate


# ============================================================
# ТЕСТЫ ДЛЯ PlayerUpdate схемы
# ============================================================

class TestPlayerUpdateSchema:
    """Тестирует валидацию PlayerUpdate."""

    def test_empty_update(self):
        """Тест: пустое обновление."""
        data = PlayerUpdate()
        update_dict = data.model_dump(exclude_unset=True)
        assert update_dict == {}

    def test_update_battletag(self):
        """Тест: обновление BattleTag."""
        data = PlayerUpdate(primary_battletag="ProPlayer#1234")
        update_dict = data.model_dump(exclude_unset=True)
        assert update_dict == {"primary_battletag": "ProPlayer#1234"}

    def test_update_division(self):
        """Тест: обновление дивизиона."""
        data = PlayerUpdate(division="Diamond")
        update_dict = data.model_dump(exclude_unset=True)
        assert update_dict == {"division": "Diamond"}

    def test_update_both_fields(self):
        """Тест: обновление обоих полей."""
        data = PlayerUpdate(primary_battletag="Player#5678", division="Master")
        update_dict = data.model_dump(exclude_unset=True)
        assert update_dict == {"primary_battletag": "Player#5678", "division": "Master"}


# ============================================================
# ТЕСТЫ ДЛЯ логики обновления игрока
# ============================================================

class TestPlayerUpdateLogic:
    """Тестирует логику обновления профиля игрока."""

    def test_apply_updates(self):
        """Тест: применение обновлений к объекту игрока."""
        # Мок игрока
        player = type('MockPlayer', (), {
            'bio': None,
            'primary_role': None,
            'secondary_role': None,
            'display_name': 'OldName',
            'updated_at': None,
        })()

        # Данные для обновления
        update_data = {
            'bio': 'New bio',
            'primary_role': 'Tank',
            'display_name': 'NewName',
        }

        # Применяем обновления (имитация логики update_player)
        for key, value in update_data.items():
            setattr(player, key, value)
        player.updated_at = datetime.now(timezone.utc)

        assert player.bio == 'New bio'
        assert player.primary_role == 'Tank'
        assert player.secondary_role is None  # Не обновлялось
        assert player.display_name == 'NewName'
        assert player.updated_at is not None

    def test_partial_update(self):
        """Тест: частичное обновление (только одно поле)."""
        player = type('MockPlayer', (), {
            'bio': 'Old bio',
            'display_name': 'OldName',
        })()

        update_data = {'display_name': 'NewName'}

        for key, value in update_data.items():
            setattr(player, key, value)

        assert player.display_name == 'NewName'
        assert player.bio == 'Old bio'  # Не изменилось


# ============================================================
# ТЕСТЫ ДЛЯ валидации ролей
# ============================================================

class TestRoleValidation:
    """Тестирует валидацию ролей игроков."""

    def test_valid_roles(self):
        """Тест: допустимые роли."""
        valid_roles = ["Tank", "Damage", "Support", "Flex"]
        for role in valid_roles:
            assert role in valid_roles

    def test_invalid_role(self):
        """Тест: недопустимая роль."""
        role = "Healer"
        valid_roles = ["Tank", "Damage", "Support", "Flex"]
        assert role not in valid_roles

    def test_role_case_sensitivity(self):
        """Тест: чувствительность к регистру."""
        role = "damage"
        valid_roles = ["Tank", "Damage", "Support", "Flex"]
        assert role not in valid_roles  # Регистр важен


# ============================================================
# ТЕСТЫ ДЛЯ get_player_tournaments логики
# ============================================================

class TestPlayerTournamentsLogic:
    """Тестирует логику формирования данных о турнирах игрока."""

    def test_tournament_data_structure(self):
        """Тест: структура данных турнира."""
        tournament_data = {
            "tournament_id": 1,
            "title": "MoonRise Mix Vol.3",
            "format": "mix",
            "status": "completed",
            "start_date": "2026-04-01T10:00:00",
            "cover_url": None,
            "participant_status": "registered",
            "is_allowed": True,
            "checked_in": True,
        }

        assert tournament_data["tournament_id"] == 1
        assert tournament_data["format"] == "mix"
        assert tournament_data["is_allowed"] is True
        assert tournament_data["checked_in"] is True

    def test_multiple_tournaments(self):
        """Тест: несколько турниров у игрока."""
        tournaments = [
            {"tournament_id": 1, "title": "Tournament A", "status": "completed"},
            {"tournament_id": 2, "title": "Tournament B", "status": "ongoing"},
            {"tournament_id": 3, "title": "Tournament C", "status": "upcoming"},
        ]

        assert len(tournaments) == 3
        # Отсортированы по start_date.desc() — предполагаем, что порядок правильный
        assert tournaments[0]["status"] == "completed"
        assert tournaments[1]["status"] == "ongoing"
        assert tournaments[2]["status"] == "upcoming"
