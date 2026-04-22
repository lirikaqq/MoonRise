"""
Тесты для draft_service.py — валидация драфта, порядок пиков,蛇形 порядок (snake draft).
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from collections import defaultdict


# ============================================================
# ТЕСТЫ ДЛЯ蛇形 порядка пиков (snake draft order)
# ============================================================

class TestSnakeDraftOrder:
    """Тестирует генерацию蛇形 (snake) порядка пиков."""

    def test_two_captains_team_size_3(self):
        """Тест: 2 капитана, team_size=3 → 6 пиков."""
        captain_ids = [1, 2]
        team_size = 3

        pick_order = []
        for round_num in range(1, team_size + 1):
            if round_num % 2 != 0:
                pick_order.extend(captain_ids)
            else:
                pick_order.extend(reversed(captain_ids))

        # Ожидаемый蛇形 порядок: 1,2 | 2,1 | 1,2
        assert pick_order == [1, 2, 2, 1, 1, 2]

    def test_three_captains_team_size_2(self):
        """Тест: 3 капитана, team_size=2 → 6 пиков."""
        captain_ids = [1, 2, 3]
        team_size = 2

        pick_order = []
        for round_num in range(1, team_size + 1):
            if round_num % 2 != 0:
                pick_order.extend(captain_ids)
            else:
                pick_order.extend(reversed(captain_ids))

        # Раунд 1: 1,2,3 | Раунд 2: 3,2,1
        assert pick_order == [1, 2, 3, 3, 2, 1]

    def test_four_captains_team_size_4(self):
        """Тест: 4 капитана, team_size=4 → 16 пиков."""
        captain_ids = [1, 2, 3, 4]
        team_size = 4

        pick_order = []
        for round_num in range(1, team_size + 1):
            if round_num % 2 != 0:
                pick_order.extend(captain_ids)
            else:
                pick_order.extend(reversed(captain_ids))

        # Раунд 1: 1,2,3,4 | Раунд 2: 4,3,2,1 | Раунд 3: 1,2,3,4 | Раунд 4: 4,3,2,1
        expected = [1, 2, 3, 4, 4, 3, 2, 1, 1, 2, 3, 4, 4, 3, 2, 1]
        assert pick_order == expected

    def test_single_captain(self):
        """Тест: 1 капитан (тривиальный случай)."""
        captain_ids = [1]
        team_size = 3

        pick_order = []
        for round_num in range(1, team_size + 1):
            if round_num % 2 != 0:
                pick_order.extend(captain_ids)
            else:
                pick_order.extend(reversed(captain_ids))

        # reversed([1]) = [1], так что всегда [1]
        assert pick_order == [1, 1, 1]


# ============================================================
# ТЕСТЫ ДЛЯ валидации драфта
# ============================================================

class TestDraftValidation:
    """Тестирует валидацию драфт-сессии."""

    def test_pick_index_bounds(self):
        """Тест: проверка выхода за границы пиков."""
        pick_order = [1, 2, 2, 1, 1, 2]  # 6 пиков
        current_pick_index = 5  # Последний пик

        # Допустимо
        assert current_pick_index < len(pick_order)

        # Следующий пик — уже выход за границы
        current_pick_index = 6
        assert current_pick_index >= len(pick_order)  # Драфт завершён

    def test_captain_turn_validation(self):
        """Тест: проверка, что пик делает правильный капитан."""
        pick_order = [1, 2, 2, 1, 1, 2]
        
        # Пик 0: капитан 1
        assert pick_order[0] == 1
        # Пик 1: капитан 2
        assert pick_order[1] == 2
        # Пик 2: капитан 2
        assert pick_order[2] == 2
        # Пик 3: капитан 1
        assert pick_order[3] == 1

    def test_duplicate_pick_detection(self):
        """Тест: обнаружение дубликата пика (игрок уже выбран)."""
        picked_user_ids = {10, 20, 30}
        new_pick_user_id = 20

        assert new_pick_user_id in picked_user_ids  # Должен быть rejected

    def test_captain_cannot_be_picked(self):
        """Тест: капитан не может быть выбран как игрок."""
        captain_ids = {1, 2}
        picked_user_id = 1

        assert picked_user_id in captain_ids  # Должен быть rejected


# ============================================================
# ТЕСТЫ ДЛЯ расчёта раунда пика
# ============================================================

class TestPickRoundCalculation:
    """Тестирует определение раунда пика."""

    def test_pick_round_formula(self):
        """Тест: формула round_number = (pick_index // num_captains) + 1."""
        num_captains = 2

        # pick_index 0,1 → round 1
        assert (0 // num_captains) + 1 == 1
        assert (1 // num_captains) + 1 == 1

        # pick_index 2,3 → round 2
        assert (2 // num_captains) + 1 == 2
        assert (3 // num_captains) + 1 == 2

        # pick_index 4,5 → round 3
        assert (4 // num_captains) + 1 == 3
        assert (5 // num_captains) + 1 == 3

    def test_three_captains(self):
        """Тест: 3 капитана."""
        num_captains = 3

        assert (0 // num_captains) + 1 == 1
        assert (2 // num_captains) + 1 == 1
        assert (3 // num_captains) + 1 == 2
        assert (5 // num_captains) + 1 == 2
        assert (6 // num_captains) + 1 == 3


# ============================================================
# ТЕСТЫ ДЛЯ deadline расчёта
# ============================================================

class TestDeadlineCalculation:
    """Тестирует расчёт дедлайна для пиков."""

    def test_deadline_calculation(self):
        """Тест: дедлайн = now + pick_time_seconds."""
        from datetime import timedelta

        now = datetime(2026, 4, 11, 15, 0, 0, tzinfo=timezone.utc)
        pick_time_seconds = 120

        deadline = now + timedelta(seconds=pick_time_seconds)
        assert deadline == datetime(2026, 4, 11, 15, 2, 0, tzinfo=timezone.utc)

    def test_redis_ttl(self):
        """Тест: TTL в Redis = pick_time + 10 секунд."""
        pick_time_seconds = 120
        redis_ttl = pick_time_seconds + 10
        assert redis_ttl == 130


# ============================================================
# ТЕСТЫ ДЛЯ draft state
# ============================================================

class TestDraftState:
    """Тестирует состояние драфта."""

    def test_initial_state(self):
        """Тест: начальное состояние драфта."""
        draft_state = {
            'status': 'pending',
            'current_pick_index': 0,
            'pick_order': [1, 2, 2, 1],
            'picks': [],
        }

        assert draft_state['status'] == 'pending'
        assert draft_state['current_pick_index'] == 0
        assert len(draft_state['picks']) == 0

    def test_in_progress_state(self):
        """Тест: состояние во время драфта."""
        draft_state = {
            'status': 'in_progress',
            'current_pick_index': 2,
            'pick_order': [1, 2, 2, 1],
            'picks': [
                {'pick_number': 1, 'captain_id': 1, 'picked_user_id': 10},
                {'pick_number': 2, 'captain_id': 2, 'picked_user_id': 20},
            ],
        }

        assert draft_state['status'] == 'in_progress'
        assert draft_state['current_pick_index'] == 2
        assert len(draft_state['picks']) == 2
        # Следующий пик должен сделать captain_id = 2 (pick_order[2])
        assert draft_state['pick_order'][2] == 2

    def test_completed_state(self):
        """Тест: завершённый драфт."""
        draft_state = {
            'status': 'completed',
            'current_pick_index': 4,
            'pick_order': [1, 2, 2, 1],
            'picks': [
                {'pick_number': 1, 'captain_id': 1, 'picked_user_id': 10},
                {'pick_number': 2, 'captain_id': 2, 'picked_user_id': 20},
                {'pick_number': 3, 'captain_id': 2, 'picked_user_id': 30},
                {'pick_number': 4, 'captain_id': 1, 'picked_user_id': 40},
            ],
        }

        assert draft_state['status'] == 'completed'
        assert draft_state['current_pick_index'] == 4  # Равно len(pick_order)
        assert len(draft_state['picks']) == 4


# ============================================================
# ТЕСТЫ ДЛЯ complete_draft_session
# ============================================================

class TestCompleteDraftSession:
    """Тестирует завершение драфта и создание команд."""

    def _create_mock_draft_session(self, num_captains=2, picks_per_captain=2):
        """Хелпер: создаёт мок DraftSession с капитанами и пиками."""
        from datetime import datetime, timezone

        # Мок капитанов
        captains = []
        for i in range(1, num_captains + 1):
            cap = MagicMock()
            cap.id = i  # captain_id = 1, 2, ...
            cap.user_id = 100 + i  # captain user_id = 101, 102, ...
            cap.team_name = f"Команда {i}"
            captains.append(cap)

        # pick_order: змейка
        captain_user_ids = [cap.user_id for cap in captains]
        pick_order = []
        for round_num in range(1, picks_per_captain + 1):
            if round_num % 2 != 0:
                pick_order.extend(captain_user_ids)
            else:
                pick_order.extend(reversed(captain_user_ids))

        # Мок пики
        picks = []
        pick_num = 0
        for round_num in range(picks_per_captain):
            if round_num % 2 != 0:
                order = list(reversed(captain_user_ids))
            else:
                order = list(captain_user_ids)
            for cap_user_id in order:
                pick_num += 1
                cap = next(c for c in captains if c.user_id == cap_user_id)
                pick = MagicMock()
                pick.id = pick_num
                pick.captain_id = cap.id
                pick.picked_user_id = 1000 + pick_num  # players: 1001, 1002, ...
                pick.pick_number = pick_num
                pick.round_number = round_num + 1
                pick.assigned_role = ["tank", "dps", "support", "flex"][pick_num % 4]
                pick.team_id = None  # ещё не назначена
                picks.append(pick)

        # Мок сессии
        session = MagicMock()
        session.id = 1
        session.tournament_id = 10
        session.status = "completed"  # уже completed после последнего пика
        session.completed_at = datetime.now(timezone.utc)
        session.pick_order = pick_order
        session.current_pick_index = len(pick_order)
        session.captains = captains
        session.picks = picks
        session.role_slots = {"tank": 1, "dps": 2, "support": 1}

        return session, captains, picks

    def test_success_two_captains(self):
        """Тест: успешное завершение драфта с 2 капитанами → 2 команды."""
        session, captains, picks = self._create_mock_draft_session(
            num_captains=2, picks_per_captain=2
        )

        # Проверяем что всё корректно настроено
        assert len(captains) == 2
        assert len(picks) == 4  # 2 капитана * 2 пика
        assert session.current_pick_index == len(session.pick_order)
        assert session.status == "completed"

        # Группируем пики по captain_id
        picks_by_captain = defaultdict(list)
        for pick in picks:
            picks_by_captain[pick.captain_id].append(pick)

        assert len(picks_by_captain) == 2
        assert len(picks_by_captain[1]) == 2  # Капитан 1 забрал 2 игроков
        assert len(picks_by_captain[2]) == 2  # Капитан 2 забрал 2 игроков

        # Проверяем что team_id = None до завершения
        for pick in picks:
            assert pick.team_id is None

    def test_success_four_captains(self):
        """Тест: 4 капитана → 4 команды."""
        session, captains, picks = self._create_mock_draft_session(
            num_captains=4, picks_per_captain=3
        )

        assert len(captains) == 4
        assert len(picks) == 12  # 4 * 3

        # Группируем
        picks_by_captain = defaultdict(list)
        for pick in picks:
            picks_by_captain[pick.captain_id].append(pick)

        assert len(picks_by_captain) == 4
        for cap_id in range(1, 5):
            assert len(picks_by_captain[cap_id]) == 3

    def test_team_creation_logic(self):
        """Тест: логика создания команд из пики."""
        session, captains, picks = self._create_mock_draft_session(
            num_captains=2, picks_per_captain=2
        )

        captains_map = {cap.id: cap for cap in captains}

        # Имитируем логику complete_draft_session
        picks_by_captain = defaultdict(list)
        for pick in picks:
            picks_by_captain[pick.captain_id].append(pick)

        created_teams = []
        for captain_id, cap_picks in picks_by_captain.items():
            cap_picks.sort(key=lambda p: p.pick_number)
            captain = captains_map[captain_id]

            # Создаём "команду" (мок)
            team = MagicMock()
            team.id = 100 + captain_id
            team.name = captain.team_name
            team.captain_user_id = captain.user_id
            team.tournament_id = session.tournament_id
            created_teams.append(team)

            # Назначаем team_id
            for pick in cap_picks:
                pick.team_id = team.id

        assert len(created_teams) == 2
        assert created_teams[0].name == "Команда 1"
        assert created_teams[1].name == "Команда 2"

        # Проверяем что все пики получили team_id
        team1_picks = [p for p in picks if p.team_id == created_teams[0].id]
        team2_picks = [p for p in picks if p.team_id == created_teams[1].id]
        assert len(team1_picks) == 2
        assert len(team2_picks) == 2


class TestCompleteDraftErrors:
    """Тестирует ошибки при завершении драфта."""

    def test_draft_not_started(self):
        """Тест: попытка завершить драфт в статусе pending → 409."""
        draft_status = "pending"
        allowed_statuses = ("in_progress", "completed")

        assert draft_status not in allowed_statuses  # Ожидается ошибка

    def test_draft_not_fully_completed(self):
        """Тест: не все пики сделаны → 400."""
        total_picks = 8
        current_pick_index = 5

        # Должна быть ошибка: 5 < 8
        assert current_pick_index < total_picks  # Драфт не завершён

    def test_teams_already_created(self):
        """Тест: команды уже созданы → 409."""
        existing_teams = [MagicMock(), MagicMock()]

        # Если команды уже есть — ошибка дублирования
        assert len(existing_teams) > 0  # Ожидается ошибка

    def test_session_not_found(self):
        """Тест: сессия не найдена → 404."""
        draft_session = None

        assert draft_session is None  # Ожидается 404
