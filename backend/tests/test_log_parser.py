"""
Тесты для log_parser.py — парсинг CSV логов Overwatch.
"""
import pytest
from app.services.log_parser import (
    calculate_file_hash,
    strip_timestamp,
    parse_log,
    _compute_round_stats,
    HeroStat,
    KillEvent,
    AssistInfo,
)


# ============================================================
# ТЕСТЫ ДЛЯ calculate_file_hash
# ============================================================

class TestCalculateFileHash:
    """Тестирует хеширование файлов."""

    def test_known_hash(self):
        """Тест: хеш известного содержимого."""
        content = b"Hello, World!"
        hash_result = calculate_file_hash(content)
        # SHA-256 от "Hello, World!"
        assert hash_result == 'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'

    def test_empty_content(self):
        """Тест: хеш пустого содержимого."""
        content = b""
        hash_result = calculate_file_hash(content)
        # SHA-256 от пустой строки
        assert hash_result == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

    def test_different_content(self):
        """Тест: разное содержимое — разные хеши."""
        hash1 = calculate_file_hash(b"team1")
        hash2 = calculate_file_hash(b"team2")
        assert hash1 != hash2

    def test_bytes_input(self):
        """Тест: принимает только bytes."""
        content = b"\x00\x01\x02\x03"
        hash_result = calculate_file_hash(content)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 = 64 hex символа


# ============================================================
# ТЕСТЫ ДЛЯ strip_timestamp
# ============================================================

class TestStripTimestamp:
    """Тестирует удаление timestamp из строк лога."""

    def test_standard_timestamp(self):
        """Тест: стандартный формат [HH:MM:SS]."""
        line = "[12:34:56] match_start,SomeMap,Control"
        result = strip_timestamp(line)
        assert result == "match_start,SomeMap,Control"

    def test_no_timestamp(self):
        """Тест: строка без timestamp."""
        line = "match_start,SomeMap,Control"
        result = strip_timestamp(line)
        assert result == line

    def test_empty_string(self):
        """Тест: пустая строка."""
        result = strip_timestamp("")
        assert result == ""

    def test_partial_timestamp(self):
        """Тест: некорректный timestamp (не заменяется)."""
        line = "[12:34] match_start"
        result = strip_timestamp(line)
        # Regex ожидает [HH:MM:SS], поэтому не сработает
        assert result == "[12:34] match_start"


# ============================================================
# ТЕСТЫ ДЛЯ _compute_round_stats
# ============================================================

class TestComputeRoundStats:
    """Тестирует вычисление статистики по раундам (diff cumulative)."""

    def test_two_rounds(self):
        """Тест: два раунда, diff между ними."""
        hero = HeroStat(hero_name='Mercy', eliminations=5, final_blows=2, deaths=1, time_played=120.0)
        hero_prev = HeroStat(hero_name='Mercy', eliminations=2, final_blows=1, deaths=0, time_played=60.0)

        rounds_data = {
            1: {('Player1', 'TeamA'): {'Mercy': hero_prev}},
            2: {('Player1', 'TeamA'): {'Mercy': hero}},
        }

        result = _compute_round_stats(rounds_data)

        assert len(result) == 2
        # Раунд 1: базовые значения
        assert result[0]['round_number'] == 1
        assert result[0]['players'][0]['eliminations'] == 2
        assert result[0]['players'][0]['deaths'] == 0

        # Раунд 2: diff (5-2=3, 2-1=1, 1-0=1)
        assert result[1]['round_number'] == 2
        assert result[1]['players'][0]['eliminations'] == 3  # 5 - 2
        assert result[1]['players'][0]['final_blows'] == 1  # 2 - 1
        assert result[1]['players'][0]['deaths'] == 1  # 1 - 0

    def test_single_round(self):
        """Тест: один раунд — diff = сами значения."""
        hero = HeroStat(hero_name='Genji', eliminations=10, deaths=3, time_played=180.0)

        rounds_data = {
            1: {('Player2', 'TeamB'): {'Genji': hero}},
        }

        result = _compute_round_stats(rounds_data)

        assert len(result) == 1
        assert result[0]['round_number'] == 1
        assert result[0]['players'][0]['eliminations'] == 10
        assert result[0]['players'][0]['deaths'] == 3

    def test_empty_rounds(self):
        """Тест: пустые раунды."""
        result = _compute_round_stats({})
        assert result == []

    def test_multiple_heroes(self):
        """Тест: несколько героев у одного игрока."""
        hero1 = HeroStat(hero_name='Mercy', eliminations=3, time_played=100.0)
        hero2 = HeroStat(hero_name='Ana', eliminations=5, time_played=80.0)

        rounds_data = {
            1: {('Player1', 'TeamA'): {'Mercy': hero1, 'Ana': hero2}},
        }

        result = _compute_round_stats(rounds_data)

        assert len(result) == 1
        player = result[0]['players'][0]
        # Сумма элиминаций по всем героям
        assert player['eliminations'] == 8  # 3 + 5
        assert len(player['heroes']) == 2

    def test_zero_time_hero(self):
        """Тест: герой с time_played = 0 не включается."""
        hero_active = HeroStat(hero_name='Mercy', eliminations=3, time_played=100.0)
        hero_inactive = HeroStat(hero_name='Genji', eliminations=0, time_played=0.0)

        rounds_data = {
            1: {('Player1', 'TeamA'): {'Mercy': hero_active, 'Genji': hero_inactive}},
        }

        result = _compute_round_stats(rounds_data)

        # Только Mercy должен быть включён (Genji time_played = 0)
        assert len(result[0]['players'][0]['heroes']) == 1
        assert result[0]['players'][0]['heroes'][0]['hero_name'] == 'Mercy'


# ============================================================
# ТЕСТЫ ДЛЯ parse_log
# ============================================================

class TestParseLog:
    """Тестирует полный парсинг CSV лога."""

    def _create_log_content(self, lines: list[str]) -> bytes:
        """Хелпер: создаёт байтовое содержимое лога."""
        return "\n".join(lines).encode('utf-8')

    def test_parse_minimal_log(self):
        """Тест: минимальный лог с match_start и match_end."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Route 66,Escort,Team 1,Team 2",
            "[00:08:47] ,match_end,527.06,4,4,3",
        ])

        result = parse_log(content, "test_log.csv")

        assert result.map_name == "Route 66"
        assert result.game_mode == "Escort"
        assert result.team1_label == "Team 1"
        assert result.team2_label == "Team 2"
        assert result.duration_seconds == 527.06
        assert result.file_name == "test_log.csv"
        assert len(result.file_hash) == 64

    def test_parse_rounds_and_stats(self):
        """Тест: лог с раундами и player_stat."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Dorado,Escort,Team 1,Team 2",
            "[00:00:36] ,round_start,0,1,Team 2,0,0,0",
            "[00:08:47] ,round_end,527.06,1,Team 2,0,3,3,0,0,34.28",
            "[00:08:47] ,player_stat,527.06,1,Team 2,Squirrel,Ana,14,4,2,3402.84,76.80,3272.33,3761.82,1775.36,80.54,2424.39,0,12,7,0,0,0,0,0,5,0,0,0,0,0.54,0,0,218,105,107,126,68,0.50,527.06",
            "[00:09:28] ,round_start,527.06,2,Team 1,0,3,0",
            "[00:17:29] ,round_end,1049.06,2,Team 1,3,3,3,0,0,44.31",
            "[00:17:29] ,player_stat,1049.06,2,Team 1,Ocelot,Wrecking Ball,34,14,8,21502.00,4093.91,17408.09,0,17081.97,0,31476.87,1998.28,0,0,7,8,2,3,4,12,0,1,104,0.07,0,0,0,4342,1443,2581,0,0,0.36,1049.06",
            "[00:23:57] ,match_end,1437.06,4,4,3",
        ])

        result = parse_log(content, "rounds_test.csv")

        assert result.map_name == "Dorado"
        assert result.game_mode == "Escort"
        # players берутся из final_round (раунд 2)
        assert len(result.players) == 1
        assert result.players[0].player_name == "Ocelot"
        assert result.players[0].team_label == "Team 1"
        assert result.players[0].eliminations == 34

    def test_parse_kills(self):
        """Тест: лог с kill событиями."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Hollywood,Hybrid,Red,Blue",
            "[00:00:36] ,round_start,0,1,Red,0,0,0",
            "[00:01:53] ,kill,31.95,Red,Ocelot,Wrecking Ball,Blue,Squirrel,Ana,Crouch,56.64,0,0",
            "[00:08:47] ,match_end,527.06,1,1,0",
        ])

        result = parse_log(content, "kills_test.csv")

        assert len(result.kills) == 1
        kill = result.kills[0]
        assert kill.killer_name == "Ocelot"
        assert kill.killer_hero == "Wrecking Ball"
        assert kill.killer_team_label == "Red"
        assert kill.victim_name == "Squirrel"
        assert kill.victim_hero == "Ana"
        assert kill.victim_team_label == "Blue"
        assert kill.damage == 56.64
        assert kill.is_critical is False
        assert kill.is_headshot is False
        assert kill.round_number == 1
        assert kill.weapon == "Crouch"

    def test_parse_kills_critical(self):
        """Тест: kill с критическим ударом."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Map1,Control,T1,T2",
            "[00:00:36] ,round_start,0,1,T1,0,0,0",
            "[00:02:01] ,kill,39.42,T1,NotNumb,Reaper,T2,Kamikuje,Sigma,Primary Fire,18.65,True,0",
            "[00:05:00] ,match_end,300.0,1,1,0",
        ])

        result = parse_log(content, "crit_kill.csv")

        assert len(result.kills) == 1
        assert result.kills[0].is_critical is True
        assert result.kills[0].damage == 18.65

    def test_parse_assists(self):
        """Тест: лог с assist событиями, привязанными к киллам."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Map1,Control,TeamA,TeamB",
            "[00:00:36] ,round_start,0,1,TeamA,0,0,0",
            "[00:02:06] ,offensive_assist,44.80,TeamA,Cranbereis,Lúcio,0",
            "[00:02:06] ,kill,44.42,TeamA,Ocelot,Wrecking Ball,TeamB,DEE,Mercy,Primary Fire,7.10,True,0",
            "[00:05:00] ,match_end,300.0,1,1,0",
        ])

        result = parse_log(content, "assists_test.csv")

        assert len(result.kills) == 1
        kill = result.kills[0]
        assert len(kill.offensive_assists) == 1
        assert kill.offensive_assists[0].player_name == "Cranbereis"
        assert kill.offensive_assists[0].hero_name == "Lúcio"

    def test_parse_defensive_assists(self):
        """Тест: defensive assists."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Map2,Control,X,Y",
            "[00:00:36] ,round_start,0,1,X,0,0,0",
            "[00:01:57] ,defensive_assist,36.90,X,Cranbereis,Lúcio,0",
            "[00:01:58] ,kill,37.10,X,Cranbereis,Lúcio,Y,Player,Tracer,Primary Fire,20,0,0",
            "[00:05:00] ,match_end,300.0,1,1,0",
        ])

        result = parse_log(content, "def_assists_test.csv")

        assert len(result.kills) == 1
        assert len(result.kills[0].defensive_assists) == 1
        assert result.kills[0].defensive_assists[0].player_name == "Cranbereis"

    def test_assist_not_matched(self):
        """Тест: assist вне окна 1 секунды не привязывается."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Map3,Control,A,B",
            "[00:00:36] ,round_start,0,1,A,0,0,0",
            "[00:02:00] ,offensive_assist,40.0,A,Support,Mercy,0",
            "[00:02:05] ,kill,45.0,A,DPS,Genji,B,Victim,D.Va,Melee,100.0,False,0",
            "[00:05:00] ,match_end,300.0,1,1,0",
        ])

        result = parse_log(content, "unmatched_assist.csv")

        assert len(result.kills) == 1
        assert len(result.kills[0].offensive_assists) == 0  # 5 сек разница > 1 сек

    def test_parse_multiple_rounds_kills(self):
        """Тест: киллы в разных раундах."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Map4,Hybrid,T1,T2",
            "[00:00:36] ,round_start,0,1,T1,0,0,0",
            "[00:01:53] ,kill,31.95,T1,P1,Genji,T2,P2,Mercy,Primary Fire,100.0,False,0",
            "[00:04:00] ,round_end,240.0,1,T1,0,3,3,0,0,10.0",
            "[00:04:30] ,round_start,240.0,2,T2,3,3,0",
            "[00:05:00] ,kill,300.0,T2,P3,Reaper,T1,P4,Winston,Ability1,150.0,True,0",
            "[00:10:00] ,match_end,600.0,2,1,1",
        ])

        result = parse_log(content, "multi_round_kills.csv")

        assert len(result.kills) == 2
        assert result.kills[0].round_number == 1
        assert result.kills[1].round_number == 2

    def test_invalid_lines_skipped(self):
        """Тест: некорректные строки пропускаются."""
        content = self._create_log_content([
            "[00:00:00] ,match_start,0,Map5,Control,C,D",
            "invalid_line",
            "[00:05:00] ,match_end,300.0,1,1,0",
        ])

        result = parse_log(content, "invalid_lines.csv")

        assert result.map_name == "Map5"
        assert len(result.kills) == 0

    def test_unknown_map_and_mode(self):
        """Тест: нет match_start — дефолтные значения."""
        content = self._create_log_content([
            "[00:10:00] ,match_end,600.0,4,4,3",
        ])

        result = parse_log(content, "no_match_start.csv")

        assert result.map_name == "Unknown"
        assert result.game_mode == "Unknown"
        assert result.team1_label == "Team 1"
        assert result.team2_label == "Team 2"

    def test_file_hash_consistency(self):
        """Тест: одинаковое содержимое → одинаковый хеш."""
        content1 = self._create_log_content(["[00:00:00] ,match_start,0,Map,T1,T2"])
        content2 = self._create_log_content(["[00:00:00] ,match_start,0,Map,T1,T2"])

        result1 = parse_log(content1, "test1.csv")
        result2 = parse_log(content2, "test2.csv")

        assert result1.file_hash == result2.file_hash
