"""
Тесты для match_metrics.py — Contribution Score, MVP/SVP, First Blood, last_hero.
"""
import pytest
from unittest.mock import MagicMock

from app.services.match_metrics import (
    calculate_contribution_score,
    assign_mvp_svp,
    determine_first_bloods,
    get_last_hero,
    compute_match_metrics,
)


# ============================================================
# ТЕСТЫ ДЛЯ calculate_contribution_score
# ============================================================

class TestCalculateContributionScore:
    """Тестирует расчёт Contribution Score."""

    def test_zero_stats(self):
        """Тест: все нули — score = 0."""
        score = calculate_contribution_score(0, 0, 0, 0, 0, 0, 0, 0)
        assert score == 0.0

    def test_eliminations_only(self):
        """Тест: только элиминации (elim * 500)."""
        score = calculate_contribution_score(10, 0, 0, 0, 0, 0, 0, 0)
        assert score == 5000.0  # 10 * 500

    def test_final_blows_only(self):
        """Тест: только финальные удары (fb * 250)."""
        score = calculate_contribution_score(0, 5, 0, 0, 0, 0, 0, 0)
        assert score == 1250.0  # 5 * 250

    def test_deaths_penalty(self):
        """Тест: штрафы за смерти (deaths * -750)."""
        score = calculate_contribution_score(0, 0, 3, 0, 0, 0, 0, 0)
        assert score == -2250.0  # 3 * -750

    def test_healing_and_damage(self):
        """Тест: урон + лечение."""
        score = calculate_contribution_score(0, 0, 0, 5000, 3000, 0, 0, 0)
        assert score == 8000.0  # 5000 + 3000

    def test_blocked_damage(self):
        """Тест: заблокированный урон (blocked * 0.1)."""
        score = calculate_contribution_score(0, 0, 0, 0, 0, 2500, 0, 0)
        assert score == 250.0  # 2500 * 0.1

    def test_assists(self):
        """Тест: ассисты (assists * 50)."""
        score = calculate_contribution_score(0, 0, 0, 0, 0, 0, 4, 6)
        assert score == 500.0  # (4+6) * 50

    def test_full_formula(self):
        """Тест: полная формула."""
        # elim=5, fb=2, deaths=1, hero_dmg=3000, healing=1500, blocked=1000, off_assists=3, def_assists=2
        # CS = 5*500 + 2*250 + 5*50 + 3000 + 1500 - 1*750 + 1000*0.1
        # CS = 2500 + 500 + 250 + 3000 + 1500 - 750 + 100 = 7100
        score = calculate_contribution_score(5, 2, 1, 3000, 1500, 1000, 3, 2)
        assert score == 7100.0

    def test_rounding(self):
        """Тест: округление до 2 знаков."""
        score = calculate_contribution_score(0, 0, 0, 0, 0, 100.123, 0, 0)
        assert score == 10.01  # 100.123 * 0.1 = 10.0123 → round → 10.01


# ============================================================
# ТЕСТЫ ДЛЯ assign_mvp_svp
# ============================================================

class TestAssignMvpSvp:
    """Тестирует назначение MVP/SVP."""

    def test_basic_mvp_svp(self):
        """Тест: базовое назначение MVP (победители) и SVP (проигравшие)."""
        players = [
            {'team_id': 1, 'contribution_score': 5000, 'is_mvp': 0, 'is_svp': 0},
            {'team_id': 1, 'contribution_score': 7000, 'is_mvp': 0, 'is_svp': 0},
            {'team_id': 2, 'contribution_score': 6000, 'is_mvp': 0, 'is_svp': 0},
            {'team_id': 2, 'contribution_score': 4000, 'is_mvp': 0, 'is_svp': 0},
        ]
        assign_mvp_svp(players, winner_team_id=1)

        # Team 1 побеждает → MVP с highest score
        assert players[0]['is_mvp'] == 0
        assert players[1]['is_mvp'] == 1  # 7000 > 5000
        assert players[2]['is_mvp'] == 0
        assert players[3]['is_mvp'] == 0

        # Team 2 проигрывает → SVP с highest score
        assert players[0]['is_svp'] == 0
        assert players[1]['is_svp'] == 0
        assert players[2]['is_svp'] == 1  # 6000 > 4000
        assert players[3]['is_svp'] == 0

    def test_no_winner(self):
        """Тест: нет победителя — никто не получает MVP/SVP."""
        players = [
            {'team_id': 1, 'contribution_score': 5000, 'is_mvp': 0, 'is_svp': 0},
            {'team_id': 2, 'contribution_score': 6000, 'is_mvp': 0, 'is_svp': 0},
        ]
        assign_mvp_svp(players, winner_team_id=None)

        assert all(p['is_mvp'] == 0 and p['is_svp'] == 0 for p in players)

    def test_single_player_per_team(self):
        """Тест: по одному игроку на команду."""
        players = [
            {'team_id': 1, 'contribution_score': 3000, 'is_mvp': 0, 'is_svp': 0},
            {'team_id': 2, 'contribution_score': 2000, 'is_mvp': 0, 'is_svp': 0},
        ]
        assign_mvp_svp(players, winner_team_id=1)

        assert players[0]['is_mvp'] == 1
        assert players[1]['is_svp'] == 1

    def test_equal_scores(self):
        """Тест: равные очки — выбирается первый (max берёт первый при равенстве)."""
        players = [
            {'team_id': 1, 'contribution_score': 5000, 'is_mvp': 0, 'is_svp': 0},
            {'team_id': 1, 'contribution_score': 5000, 'is_mvp': 0, 'is_svp': 0},
        ]
        assign_mvp_svp(players, winner_team_id=1)

        # max() в Python возвращает первый элемент при равенстве
        assert players[0]['is_mvp'] == 1
        assert players[1]['is_mvp'] == 0


# ============================================================
# ТЕСТЫ ДЛЯ determine_first_bloods
# ============================================================

class TestDetermineFirstBloods:
    """Тестирует определение First Blood по раундам."""

    def test_single_round(self):
        """Тест: один раунд, несколько киллов."""
        kill1 = MagicMock(id=1, round_number=1, timestamp=10.5)
        kill2 = MagicMock(id=2, round_number=1, timestamp=5.2)  # Раньше
        kill3 = MagicMock(id=3, round_number=1, timestamp=15.0)

        result = determine_first_bloods([kill1, kill2, kill3])
        assert result == {1: 2}  # kill2 — первый в раунде 1

    def test_multiple_rounds(self):
        """Тест: несколько раундов."""
        kill1 = MagicMock(id=1, round_number=1, timestamp=10.0)
        kill2 = MagicMock(id=2, round_number=1, timestamp=5.0)
        kill3 = MagicMock(id=3, round_number=2, timestamp=20.0)
        kill4 = MagicMock(id=4, round_number=2, timestamp=18.0)  # Раньше в раунде 2
        kill5 = MagicMock(id=5, round_number=3, timestamp=30.0)

        result = determine_first_bloods([kill1, kill2, kill3, kill4, kill5])
        assert result == {1: 2, 2: 4, 3: 5}

    def test_empty_kills(self):
        """Тест: нет киллов — пустой результат."""
        result = determine_first_bloods([])
        assert result == {}

    def test_unsorted_kills(self):
        """Тест: киллы не отсортированы по времени."""
        kill1 = MagicMock(id=10, round_number=1, timestamp=50.0)
        kill2 = MagicMock(id=20, round_number=1, timestamp=10.0)  # Первый
        kill3 = MagicMock(id=30, round_number=1, timestamp=30.0)

        result = determine_first_bloods([kill1, kill3, kill2])
        assert result == {1: 20}


# ============================================================
# ТЕСТЫ ДЛЯ get_last_hero
# ============================================================

class TestGetLastHero:
    """Тестирует определение последнего героя (по time_played)."""

    def test_basic(self):
        """Тест: три героя, выбирается с максимальным time_played."""
        hero1 = MagicMock(hero_name='Mercy', time_played=100.0)
        hero2 = MagicMock(hero_name='Genji', time_played=300.0)
        hero3 = MagicMock(hero_name='D.Va', time_played=200.0)

        result = get_last_hero([hero1, hero2, hero3])
        assert result == 'Genji'

    def test_empty_list(self):
        """Тест: пустой список — None."""
        result = get_last_hero([])
        assert result is None

    def test_single_hero(self):
        """Тест: один герой."""
        hero = MagicMock(hero_name='Ana', time_played=50.0)
        result = get_last_hero([hero])
        assert result == 'Ana'


# ============================================================
# ТЕСТЫ ДЛЯ compute_match_metrics
# ============================================================

class TestComputeMatchMetrics:
    """Тестирует полный пайплайн расчёта метрик."""

    def test_full_pipeline(self):
        """Тест: полный расчёт для 4 игроков."""
        players = [
            {
                'team_id': 1,
                'eliminations': 10, 'final_blows': 3, 'deaths': 2,
                'hero_damage_dealt': 5000, 'healing_dealt': 2000,
                'damage_blocked': 1000, 'offensive_assists': 2, 'defensive_assists': 1,
                'heroes': [MagicMock(hero_name='Mercy', time_played=300)],
            },
            {
                'team_id': 1,
                'eliminations': 5, 'final_blows': 1, 'deaths': 4,
                'hero_damage_dealt': 3000, 'healing_dealt': 1000,
                'damage_blocked': 500, 'offensive_assists': 1, 'defensive_assists': 0,
                'heroes': [MagicMock(hero_name='Genji', time_played=200)],
            },
            {
                'team_id': 2,
                'eliminations': 8, 'final_blows': 2, 'deaths': 3,
                'hero_damage_dealt': 4000, 'healing_dealt': 1500,
                'damage_blocked': 800, 'offensive_assists': 3, 'defensive_assists': 2,
                'heroes': [MagicMock(hero_name='D.Va', time_played=250)],
            },
            {
                'team_id': 2,
                'eliminations': 2, 'final_blows': 0, 'deaths': 6,
                'hero_damage_dealt': 1000, 'healing_dealt': 500,
                'damage_blocked': 200, 'offensive_assists': 0, 'defensive_assists': 1,
                'heroes': [MagicMock(hero_name='Ana', time_played=150)],
            },
        ]

        result = compute_match_metrics(players, winner_team_id=1)

        # Проверяем, что contribution_score рассчитан
        # P1: 10*500 + 3*250 + 3*50 + 5000 + 2000 - 2*750 + 1000*0.1 = 5000+750+150+5000+2000-1500+100 = 11500
        assert result[0]['contribution_score'] == 11500.0
        # P2: 5*500 + 1*250 + 1*50 + 3000 + 1000 - 4*750 + 500*0.1 = 2500+250+50+3000+1000-3000+50 = 3850
        assert result[1]['contribution_score'] == 3850.0
        # P3: 8*500 + 2*250 + 5*50 + 4000 + 1500 - 3*750 + 800*0.1 = 4000+500+250+4000+1500-2250+80 = 8080
        assert result[2]['contribution_score'] == 8080.0
        # P4: 2*500 + 0*250 + 1*50 + 1000 + 500 - 6*750 + 200*0.1 = 1000+0+50+1000+500-4500+20 = -1930
        assert result[3]['contribution_score'] == -1930.0

        # MVP: лучший из победителей (team 1) → P1 (11500 > 3850)
        assert result[0]['is_mvp'] == 1
        assert result[1]['is_mvp'] == 0

        # SVP: лучший из проигравших (team 2) → P3 (8080 > -1930)
        assert result[2]['is_svp'] == 1
        assert result[3]['is_svp'] == 0

        # last_hero
        assert result[0]['last_hero'] == 'Mercy'
        assert result[1]['last_hero'] == 'Genji'
        assert result[2]['last_hero'] == 'D.Va'
        assert result[3]['last_hero'] == 'Ana'

    def test_no_heroes(self):
        """Тест: игроки без героев."""
        players = [
            {
                'team_id': 1,
                'eliminations': 0, 'final_blows': 0, 'deaths': 0,
                'hero_damage_dealt': 0, 'healing_dealt': 0,
                'damage_blocked': 0, 'offensive_assists': 0, 'defensive_assists': 0,
                'heroes': [],
            },
        ]
        result = compute_match_metrics(players, winner_team_id=1)
        assert result[0]['last_hero'] is None
        assert result[0]['contribution_score'] == 0.0
        assert result[0]['is_mvp'] == 1  # Единственный игрок в победителях
