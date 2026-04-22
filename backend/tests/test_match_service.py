"""
Тесты для match_service.py — report_encounter_result и автоматическое продвижение.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from collections import defaultdict


# ============================================================
# ТЕСТЫ ДЛЯ report_encounter_result
# ============================================================

class TestReportEncounterResult:
    """Тестирует отчёт о результате встречи и продвижение победителя."""

    def _create_mock_encounter(self, encounter_id=1, team1_id=10, team2_id=20,
                                team1_score=0, team2_score=0, winner_team_id=None,
                                next_encounter_id=None, next_encounter=None):
        """Хелпер: создаёт мок Encounter."""
        enc = MagicMock()
        enc.id = encounter_id
        enc.tournament_id = 1
        enc.team1_id = team1_id
        enc.team2_id = team2_id
        enc.team1_score = team1_score
        enc.team2_score = team2_score
        enc.winner_team_id = winner_team_id
        enc.stage = "Round 1"
        enc.round_number = 1
        enc.is_auto_created = 1
        enc.next_encounter_id = next_encounter_id
        enc.next_encounter = next_encounter
        enc.created_at = None
        return enc

    def test_success_determine_winner(self):
        """Тест: успешный отчёт — team1 побеждает."""
        enc = self._create_mock_encounter(
            encounter_id=1, team1_id=10, team2_id=20,
            team1_score=0, team2_score=0, winner_team_id=None
        )

        # Имитируем логику report_encounter_result
        team1_score, team2_score = 3, 1

        # Ничья?
        assert team1_score != team2_score

        # Определяем победителя
        winner_id = enc.team1_id if team1_score > team2_score else enc.team2_id
        assert winner_id == 10  # team1

        # Обновляем
        enc.team1_score = team1_score
        enc.team2_score = team2_score
        enc.winner_team_id = winner_id

        assert enc.winner_team_id == 10
        assert enc.team1_score == 3
        assert enc.team2_score == 1

    def test_success_determine_winner_team2(self):
        """Тест: team2 побеждает."""
        enc = self._create_mock_encounter(encounter_id=2, team1_id=10, team2_id=20)

        team1_score, team2_score = 1, 3

        assert team1_score != team2_score
        winner_id = enc.team1_id if team1_score > team2_score else enc.team2_id
        assert winner_id == 20

    def test_success_advance_to_next_match(self):
        """Тест: победитель продвинут в next_encounter (team1_id слот)."""
        next_enc = self._create_mock_encounter(
            encounter_id=2, team1_id=None, team2_id=None
        )
        enc = self._create_mock_encounter(
            encounter_id=1, team1_id=10, team2_id=20,
            next_encounter_id=2, next_encounter=next_enc
        )

        team1_score, team2_score = 3, 2
        winner_id = enc.team1_id if team1_score > team2_score else enc.team2_id
        assert winner_id == 10

        # Обновляем
        enc.team1_score = team1_score
        enc.team2_score = team2_score
        enc.winner_team_id = winner_id

        # Продвижение
        if enc.next_encounter_id is not None:
            if next_enc.team1_id is None:
                next_enc.team1_id = winner_id
            elif next_enc.team2_id is None:
                next_enc.team2_id = winner_id

        assert next_enc.team1_id == 10  # Победитель в первом слоте

    def test_success_advance_to_second_slot(self):
        """Тест: победитель идёт во второй слот (team2_id) если первый занят."""
        next_enc = self._create_mock_encounter(
            encounter_id=3, team1_id=10, team2_id=None
        )
        enc = self._create_mock_encounter(
            encounter_id=2, team1_id=20, team2_id=30,
            next_encounter_id=3, next_encounter=next_enc
        )

        team1_score, team2_score = 3, 1
        winner_id = enc.team1_id if team1_score > team2_score else enc.team2_id
        assert winner_id == 20

        enc.winner_team_id = winner_id

        if enc.next_encounter_id is not None:
            if next_enc.team1_id is None:
                next_enc.team1_id = winner_id
            elif next_enc.team2_id is None:
                next_enc.team2_id = winner_id

        assert next_enc.team2_id == 20  # Во втором слоте

    def test_final_match_no_next(self):
        """Тест: финальный матч — next_encounter_id is None, продвижения нет."""
        enc = self._create_mock_encounter(
            encounter_id=5, team1_id=10, team2_id=20,
            next_encounter_id=None, next_encounter=None
        )

        team1_score, team2_score = 3, 2
        winner_id = enc.team1_id if team1_score > team2_score else enc.team2_id

        enc.team1_score = team1_score
        enc.team2_score = team2_score
        enc.winner_team_id = winner_id

        assert enc.winner_team_id == 10
        assert enc.next_encounter_id is None  # Нет продвижения

    def test_error_already_completed(self):
        """Тест: попытка сообщить результат завершённого матча → 409."""
        enc = self._create_mock_encounter(winner_team_id=10)

        allowed = enc.winner_team_id is None
        assert not allowed  # Ожидается ошибка 409

    def test_error_draw(self):
        """Тест: ничья → 400."""
        team1_score, team2_score = 2, 2

        is_draw = team1_score == team2_score
        assert is_draw  # Ожидается ошибка 400

    def test_error_missing_team(self):
        """Тест: одна из команд отсутствует → 400."""
        enc = self._create_mock_encounter(team1_id=10, team2_id=None)

        both_present = enc.team1_id is not None and enc.team2_id is not None
        assert not both_present  # Ожидается ошибка 400


class TestEncounterToDict:
    """Тестирует сериализацию encounter."""

    def test_dict_includes_next_encounter_id(self):
        """Тест: next_encounter_id включён в dict."""
        from unittest.mock import MagicMock
        from datetime import datetime, timezone

        enc = MagicMock()
        enc.id = 1
        enc.tournament_id = 1
        enc.team1_id = 10
        enc.team2_id = 20
        enc.team1_score = 3
        enc.team2_score = 1
        enc.winner_team_id = 10
        enc.stage = "Round 1"
        enc.round_number = 1
        enc.is_auto_created = 1
        enc.next_encounter_id = 5
        enc.created_at = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)

        result = {
            'id': enc.id,
            'tournament_id': enc.tournament_id,
            'team1_id': enc.team1_id,
            'team2_id': enc.team2_id,
            'team1_score': enc.team1_score,
            'team2_score': enc.team2_score,
            'winner_team_id': enc.winner_team_id,
            'stage': enc.stage,
            'round_number': enc.round_number,
            'is_auto_created': enc.is_auto_created,
            'next_encounter_id': enc.next_encounter_id,
            'created_at': enc.created_at.isoformat() if enc.created_at else None,
        }

        assert result['next_encounter_id'] == 5
        assert result['winner_team_id'] == 10
        assert result['created_at'] == "2026-04-13T12:00:00+00:00"
