"""
Упрощенные тесты для stage_service.py
Тестируем только чистую логику без моков БД.
"""
import pytest
from unittest.mock import MagicMock

from app.services.stage_service import StageService
from app.models.tournament_stage import StageFormat, SeedingRule


# ============================================================
# ТЕСТЫ ДЛЯ _apply_upper_lower_split
# ============================================================

class TestApplyUpperLowerSplit:
    """Тестирует разделение участников на верхнюю/нижнюю сетки."""

    def test_basic_split(self):
        """Тест: базовое разделение 1-2 вверх, 3-4 вниз."""
        participants = []
        for i in range(1, 6):
            p = MagicMock()
            p.id = i
            p.seed = i
            participants.append({
                "participant": p,
                "rank": i,
                "group": "A",
                "points": (5 - i) * 3
            })

        rule_params = {
            "upper_bracket_ranks": [1, 2],
            "lower_bracket_ranks": [3, 4]
        }

        upper, lower = StageService._apply_upper_lower_split(
            participants, rule_params, 4
        )

        assert len(upper) == 2
        assert len(lower) == 2
        assert upper[0].id == 1  # Ранг 1
        assert upper[1].id == 2  # Ранг 2
        assert lower[0].id == 3  # Ранг 3
        assert lower[1].id == 4  # Ранг 4

    def test_multiple_groups(self):
        """Тест: разделение с несколькими группами."""
        participants = []
        
        # Группа A
        for i in range(1, 5):
            p = MagicMock()
            p.id = i
            p.seed = i
            participants.append({
                "participant": p,
                "rank": i,
                "group": "A",
                "points": (5 - i) * 3
            })

        # Группа B
        for i in range(1, 5):
            p = MagicMock()
            p.id = 10 + i
            p.seed = i
            participants.append({
                "participant": p,
                "rank": i,
                "group": "B",
                "points": (5 - i) * 3
            })

        rule_params = {
            "upper_bracket_ranks": [1, 2],
            "lower_bracket_ranks": [3, 4]
        }

        upper, lower = StageService._apply_upper_lower_split(
            participants, rule_params, 4
        )

        # 4 участника с рангом 1-2 из A и 4 из B
        assert len(upper) == 4
        assert len(lower) == 4
        
        upper_ids = {p.id for p in upper}
        assert upper_ids == {1, 2, 11, 12}  # Ранги 1-2 из обеих групп


# ============================================================
# ТЕСТЫ ДЛЯ _apply_cross_group_seeding
# ============================================================

class TestApplyCrossGroupSeeding:
    """Тестирует перекрестный посев."""

    def test_basic_cross_seeding(self):
        """Тест: базовый перекрестный посев A1, B1, A2, B2."""
        # Группа A
        group_a = []
        for i in range(1, 4):
            p = MagicMock()
            p.id = i
            p.seed = i
            group_a.append({
                "participant": p,
                "rank": i,
                "group": "Группа A",
                "points": (4 - i) * 3
            })

        # Группа B
        group_b = []
        for i in range(1, 4):
            p = MagicMock()
            p.id = 10 + i
            p.seed = i
            group_b.append({
                "participant": p,
                "rank": i,
                "group": "Группа B",
                "points": (4 - i) * 3
            })

        participants = group_a + group_b
        mock_stage = MagicMock()

        result = StageService._apply_cross_group_seeding(
            participants, mock_stage, {}
        )

        # Ожидаемый порядок: A1, B1, A2, B2, A3, B3
        assert len(result) == 6
        assert result[0].id == 1   # A1
        assert result[1].id == 11  # B1
        assert result[2].id == 2   # A2
        assert result[3].id == 12  # B2
        assert result[4].id == 3   # A3
        assert result[5].id == 13  # B3

    def test_uneven_groups(self):
        """Тест: перекрестный посев с неравномерными группами."""
        # Группа A (4 участника)
        group_a = []
        for i in range(1, 5):
            p = MagicMock()
            p.id = i
            p.seed = i
            group_a.append({
                "participant": p,
                "rank": i,
                "group": "A",
                "points": (5 - i) * 3
            })

        # Группа B (2 участника)
        group_b = []
        for i in range(1, 3):
            p = MagicMock()
            p.id = 10 + i
            p.seed = i
            group_b.append({
                "participant": p,
                "rank": i,
                "group": "B",
                "points": (3 - i) * 3
            })

        participants = group_a + group_b
        mock_stage = MagicMock()

        result = StageService._apply_cross_group_seeding(
            participants, mock_stage, {}
        )

        # A1, B1, A2, B2, A3, A4
        assert len(result) == 6
        assert result[0].id == 1   # A1
        assert result[1].id == 11  # B1
        assert result[2].id == 2   # A2
        assert result[3].id == 12  # B2
        assert result[4].id == 3   # A3
        assert result[5].id == 4   # A4


# ============================================================
# ТЕСТЫ ДЛЯ combinations (Round Robin логика)
# ============================================================

class TestRoundRobinCombinations:
    """Тестируем логику combinations для Round Robin."""

    def test_combinations_count(self):
        """Тест: правильное количество комбинаий."""
        from itertools import combinations
        
        # 5 участников: C(5,2) = 10
        participants_5 = list(range(5))
        assert len(list(combinations(participants_5, 2))) == 10

        # 4 участника: C(4,2) = 6
        participants_4 = list(range(4))
        assert len(list(combinations(participants_4, 2))) == 6

        # 3 участника: C(3,2) = 3
        participants_3 = list(range(3))
        assert len(list(combinations(participants_3, 2))) == 3

    def test_uneven_groups_total(self):
        """Тест: общее количество матчей в неравномерных группах."""
        from itertools import combinations
        
        # Группа A: 5 участников = 10 матчей
        # Группа B: 4 участника = 6 матчей
        # Всего: 16
        group_a_matches = len(list(combinations(range(5), 2)))
        group_b_matches = len(list(combinations(range(4), 2)))
        
        assert group_a_matches == 10
        assert group_b_matches == 6
        assert group_a_matches + group_b_matches == 16
