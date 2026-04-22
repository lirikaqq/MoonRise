import hashlib
import re
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AssistInfo:
    player_name: str
    team_label: str
    hero_name: str
    assist_type: str  # 'offensive' or 'defensive'


@dataclass
class KillEvent:
    timestamp: float
    round_number: int
    killer_name: str
    killer_team_label: str
    killer_hero: str
    victim_name: str
    victim_team_label: str
    victim_hero: str
    weapon: str
    damage: float
    is_critical: bool
    is_headshot: bool
    offensive_assists: list = field(default_factory=list)  # list of AssistInfo
    defensive_assists: list = field(default_factory=list)


@dataclass
class HeroStat:
    hero_name: str
    eliminations: int = 0
    final_blows: int = 0
    deaths: int = 0
    all_damage_dealt: float = 0
    barrier_damage_dealt: float = 0
    hero_damage_dealt: float = 0
    healing_dealt: float = 0
    healing_received: float = 0
    self_healing: float = 0
    damage_taken: float = 0
    damage_blocked: float = 0
    defensive_assists: int = 0
    offensive_assists: int = 0
    ultimates_earned: int = 0
    ultimates_used: int = 0
    multikill_best: int = 0
    multikills: int = 0
    solo_kills: int = 0
    objective_kills: int = 0
    environmental_kills: int = 0
    environmental_deaths: int = 0
    critical_hits: int = 0
    critical_hit_accuracy: float = 0
    scoped_accuracy: float = 0
    scoped_critical_hit_accuracy: float = 0
    scoped_critical_hit_kills: int = 0
    shots_fired: int = 0
    shots_hit: int = 0
    shots_missed: int = 0
    scoped_shots_fired: int = 0
    scoped_shots_hit: int = 0
    weapon_accuracy: float = 0
    time_played: float = 0


@dataclass
class PlayerStat:
    player_name: str
    team_label: str
    eliminations: int = 0
    final_blows: int = 0
    deaths: int = 0
    all_damage_dealt: float = 0
    hero_damage_dealt: float = 0
    healing_dealt: float = 0
    healing_received: float = 0
    self_healing: float = 0
    damage_taken: float = 0
    damage_blocked: float = 0
    defensive_assists: int = 0
    offensive_assists: int = 0
    objective_kills: int = 0
    ultimates_earned: int = 0
    ultimates_used: int = 0
    time_played: float = 0
    weapon_accuracy: float = 0
    heroes: list = field(default_factory=list)


@dataclass
class ParsedMatch:
    map_name: str
    game_mode: str
    team1_label: str
    team2_label: str
    winner_label: Optional[str]
    duration_seconds: float
    players: list
    file_hash: str
    file_name: str
    round_stats: list = field(default_factory=list)
    kills: list = field(default_factory=list)  # list of KillEvent
    parse_warnings: list[str] = field(default_factory=list)


def calculate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def strip_timestamp(line: str) -> str:
    return re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*', '', line)


STAT_INDEX_MAP = {
    'eliminations': 4, 'final_blows': 5, 'deaths': 6,
    'all_damage_dealt': 7, 'barrier_damage_dealt': 8, 'hero_damage_dealt': 9,
    'healing_dealt': 10, 'healing_received': 11, 'self_healing': 12,
    'damage_taken': 13, 'damage_blocked': 14,
    'defensive_assists': 15, 'offensive_assists': 16,
    'ultimates_earned': 17, 'ultimates_used': 18,
    'multikill_best': 19, 'multikills': 20, 'solo_kills': 21,
    'objective_kills': 22, 'environmental_kills': 23, 'environmental_deaths': 24,
    'critical_hits': 25, 'critical_hit_accuracy': 26,
    'scoped_accuracy': 27, 'scoped_critical_hit_accuracy': 28, 'scoped_critical_hit_kills': 29,
    'shots_fired': 30, 'shots_hit': 31, 'shots_missed': 32,
    'scoped_shots_fired': 33, 'scoped_shots_hit': 34,
    'weapon_accuracy': 35, 'time_played': 36,
}

ADDITIVE_FIELDS = [
    'eliminations', 'final_blows', 'deaths',
    'all_damage_dealt', 'barrier_damage_dealt', 'hero_damage_dealt',
    'healing_dealt', 'healing_received', 'self_healing',
    'damage_taken', 'damage_blocked',
    'defensive_assists', 'offensive_assists',
    'objective_kills', 'ultimates_earned', 'ultimates_used',
    'multikill_best', 'multikills', 'solo_kills',
    'environmental_kills', 'environmental_deaths',
    'critical_hits', 'shots_fired', 'shots_hit', 'shots_missed',
    'scoped_shots_fired', 'scoped_shots_hit', 'scoped_critical_hit_kills',
    'time_played',
]


def _compute_round_stats(rounds_data):
    round_numbers = sorted(rounds_data.keys())
    if not round_numbers:
        return []

    result = []
    for i, rnd in enumerate(round_numbers):
        prev_rnd = round_numbers[i - 1] if i > 0 else None
        round_players = []

        for (player_name, team_label), heroes_dict in rounds_data[rnd].items():
            player_heroes = []

            for hero_name, hero in heroes_dict.items():
                prev_hero = None
                if prev_rnd:
                    prev_heroes = rounds_data.get(prev_rnd, {}).get((player_name, team_label), {})
                    prev_hero = prev_heroes.get(hero_name)

                hero_data = {'hero_name': hero_name}
                for fld in ADDITIVE_FIELDS:
                    cur = getattr(hero, fld, 0) or 0
                    prev = getattr(prev_hero, fld, 0) if prev_hero else 0
                    hero_data[fld] = round(cur - prev, 2)

                sf = hero_data.get('shots_fired', 0)
                sh = hero_data.get('shots_hit', 0)
                hero_data['weapon_accuracy'] = round(sh / sf, 4) if sf > 0 else 0

                if hero_data['time_played'] > 0:
                    player_heroes.append(hero_data)

            if not player_heroes:
                continue

            player_data = {'player_name': player_name, 'team_label': team_label, 'heroes': player_heroes}
            for fld in ADDITIVE_FIELDS:
                player_data[fld] = round(sum(h.get(fld, 0) for h in player_heroes), 2)

            tf = sum(h.get('shots_fired', 0) for h in player_heroes)
            th = sum(h.get('shots_hit', 0) for h in player_heroes)
            player_data['weapon_accuracy'] = round(th / tf, 4) if tf > 0 else 0

            round_players.append(player_data)

        if round_players:
            result.append({'round_number': rnd, 'players': round_players})

    return result


def parse_log(content: bytes, file_name: str) -> ParsedMatch:
    file_hash = calculate_file_hash(content)
    text = content.decode('utf-8', errors='replace')
    lines = text.splitlines()

    map_name = "Unknown"
    game_mode = "Unknown"
    team1_label = "Team 1"
    team2_label = "Team 2"
    duration_seconds = 0.0
    winner_label = None
    last_round = 0
    rounds_data: dict[int, dict[tuple, dict[str, HeroStat]]] = {}

    # Kill feed tracking
    kills: list[KillEvent] = []
    pending_assists: list = []  # assists not yet matched to kills
    current_round = 0
    bad_lines = 0

    def safe_float(data, idx):
        try:
            val = data[idx].strip()
            return float(val) if val not in ('', 'True', 'False', '****') else 0.0
        except (ValueError, IndexError):
            return 0.0

    def safe_int(data, idx):
        try:
            val = data[idx].strip()
            return int(float(val)) if val not in ('', 'True', 'False', '****') else 0
        except (ValueError, IndexError):
            return 0

    for raw_line in lines:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        line = strip_timestamp(raw_line)
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 2:
            continue

        event_type = parts[1]

        if event_type == 'match_start' and len(parts) >= 7:
            map_name = parts[3]
            game_mode = parts[4]
            team1_label = parts[5]
            team2_label = parts[6]

        elif event_type == 'match_end' and len(parts) >= 3:
            try:
                duration_seconds = float(parts[2])
            except (ValueError, IndexError):
                pass

        elif event_type == 'round_end' and len(parts) >= 5:
            try:
                round_num = int(parts[3])
                w = parts[4].strip()
                if w:
                    winner_label = w
                last_round = max(last_round, round_num)
            except (ValueError, IndexError):
                pass

        elif event_type == 'round_start' and len(parts) >= 4:
            try:
                current_round = int(parts[3])
            except (ValueError, IndexError):
                pass

        elif event_type == 'kill' and len(parts) >= 13:
            try:
                kill_time = float(parts[2])
                killer_team = parts[3].strip()
                killer_name = parts[4].strip()
                killer_hero = parts[5].strip()
                victim_team = parts[6].strip()
                victim_name = parts[7].strip()
                victim_hero = parts[8].strip()
                weapon = parts[9].strip()
                damage = float(parts[10]) if parts[10] else 0.0
                is_crit = parts[11].strip() == 'True'
                is_hs = parts[12].strip() == 'True'

                kill = KillEvent(
                    timestamp=kill_time,
                    round_number=current_round,
                    killer_name=killer_name,
                    killer_team_label=killer_team,
                    killer_hero=killer_hero,
                    victim_name=victim_name,
                    victim_team_label=victim_team,
                    victim_hero=victim_hero,
                    weapon=weapon,
                    damage=damage,
                    is_critical=is_crit,
                    is_headshot=is_hs,
                )

                # Match pending assists (within 1 second window)
                for a in pending_assists[:]:
                    if abs(a['timestamp'] - kill_time) <= 1.0:
                        assist_info = AssistInfo(
                            player_name=a['player_name'],
                            team_label=a['team_label'],
                            hero_name=a['hero_name'],
                            assist_type=a['assist_type'],
                        )
                        if a['assist_type'] == 'offensive':
                            kill.offensive_assists.append(assist_info)
                        else:
                            kill.defensive_assists.append(assist_info)
                        pending_assists.remove(a)

                kills.append(kill)
            except Exception as e:
                bad_lines += 1
                logger.warning(f"Skipped malformed line [kill]: {e} | line: {raw_line[:120]}")
                continue

        elif event_type in ('defensive_assist', 'offensive_assist') and len(parts) >= 6:
            try:
                assist_time = float(parts[2])
                assist_team = parts[3].strip()
                assist_player = parts[4].strip()
                assist_hero = parts[5].strip()
                pending_assists.append({
                    'timestamp': assist_time,
                    'player_name': assist_player,
                    'team_label': assist_team,
                    'hero_name': assist_hero,
                    'assist_type': 'offensive' if event_type == 'offensive_assist' else 'defensive',
                })
            except Exception as e:
                bad_lines += 1
                logger.warning(f"Skipped malformed line [{event_type}]: {e} | line: {raw_line[:120]}")
                continue

        elif event_type == 'player_stat' and len(parts) >= 40:
            try:
                round_num = int(parts[3])
                team = parts[4].strip()
                player_name = parts[5].strip()
                hero_name = parts[6].strip()
                data = parts[3:]

                hero = HeroStat(
                    hero_name=hero_name,
                    eliminations=safe_int(data, STAT_INDEX_MAP['eliminations']),
                    final_blows=safe_int(data, STAT_INDEX_MAP['final_blows']),
                    deaths=safe_int(data, STAT_INDEX_MAP['deaths']),
                    all_damage_dealt=safe_float(data, STAT_INDEX_MAP['all_damage_dealt']),
                    barrier_damage_dealt=safe_float(data, STAT_INDEX_MAP['barrier_damage_dealt']),
                    hero_damage_dealt=safe_float(data, STAT_INDEX_MAP['hero_damage_dealt']),
                    healing_dealt=safe_float(data, STAT_INDEX_MAP['healing_dealt']),
                    healing_received=safe_float(data, STAT_INDEX_MAP['healing_received']),
                    self_healing=safe_float(data, STAT_INDEX_MAP['self_healing']),
                    damage_taken=safe_float(data, STAT_INDEX_MAP['damage_taken']),
                    damage_blocked=safe_float(data, STAT_INDEX_MAP['damage_blocked']),
                    defensive_assists=safe_int(data, STAT_INDEX_MAP['defensive_assists']),
                    offensive_assists=safe_int(data, STAT_INDEX_MAP['offensive_assists']),
                    ultimates_earned=safe_int(data, STAT_INDEX_MAP['ultimates_earned']),
                    ultimates_used=safe_int(data, STAT_INDEX_MAP['ultimates_used']),
                    multikill_best=safe_int(data, STAT_INDEX_MAP['multikill_best']),
                    multikills=safe_int(data, STAT_INDEX_MAP['multikills']),
                    solo_kills=safe_int(data, STAT_INDEX_MAP['solo_kills']),
                    objective_kills=safe_int(data, STAT_INDEX_MAP['objective_kills']),
                    environmental_kills=safe_int(data, STAT_INDEX_MAP['environmental_kills']),
                    environmental_deaths=safe_int(data, STAT_INDEX_MAP['environmental_deaths']),
                    critical_hits=safe_int(data, STAT_INDEX_MAP['critical_hits']),
                    critical_hit_accuracy=safe_float(data, STAT_INDEX_MAP['critical_hit_accuracy']),
                    scoped_accuracy=safe_float(data, STAT_INDEX_MAP['scoped_accuracy']),
                    scoped_critical_hit_accuracy=safe_float(data, STAT_INDEX_MAP['scoped_critical_hit_accuracy']),
                    scoped_critical_hit_kills=safe_int(data, STAT_INDEX_MAP['scoped_critical_hit_kills']),
                    shots_fired=safe_int(data, STAT_INDEX_MAP['shots_fired']),
                    shots_hit=safe_int(data, STAT_INDEX_MAP['shots_hit']),
                    shots_missed=safe_int(data, STAT_INDEX_MAP['shots_missed']),
                    scoped_shots_fired=safe_int(data, STAT_INDEX_MAP['scoped_shots_fired']),
                    scoped_shots_hit=safe_int(data, STAT_INDEX_MAP['scoped_shots_hit']),
                    weapon_accuracy=safe_float(data, STAT_INDEX_MAP['weapon_accuracy']),
                    time_played=safe_float(data, STAT_INDEX_MAP['time_played']),
                )

                if round_num not in rounds_data:
                    rounds_data[round_num] = {}
                key = (player_name, team)
                if key not in rounds_data[round_num]:
                    rounds_data[round_num][key] = {}

                existing = rounds_data[round_num][key].get(hero_name)
                if existing is None or hero.time_played > existing.time_played:
                    rounds_data[round_num][key][hero_name] = hero
            except Exception as e:
                bad_lines += 1
                logger.warning(f"Skipped malformed line [player_stat]: {e} | line: {raw_line[:120]}")
                continue

    final_round = last_round if last_round > 0 else (max(rounds_data.keys()) if rounds_data else 0)

    players = []
    final_data = rounds_data.get(final_round, {})

    for (player_name, team_label), heroes_dict in final_data.items():
        ps = PlayerStat(player_name=player_name, team_label=team_label)
        ps.heroes = list(heroes_dict.values())
        ps.eliminations = sum(h.eliminations for h in ps.heroes)
        ps.final_blows = sum(h.final_blows for h in ps.heroes)
        ps.deaths = sum(h.deaths for h in ps.heroes)
        ps.all_damage_dealt = sum(h.all_damage_dealt for h in ps.heroes)
        ps.hero_damage_dealt = sum(h.hero_damage_dealt for h in ps.heroes)
        ps.healing_dealt = sum(h.healing_dealt for h in ps.heroes)
        ps.healing_received = sum(h.healing_received for h in ps.heroes)
        ps.self_healing = sum(h.self_healing for h in ps.heroes)
        ps.damage_taken = sum(h.damage_taken for h in ps.heroes)
        ps.damage_blocked = sum(h.damage_blocked for h in ps.heroes)
        ps.defensive_assists = sum(h.defensive_assists for h in ps.heroes)
        ps.offensive_assists = sum(h.offensive_assists for h in ps.heroes)
        ps.objective_kills = sum(h.objective_kills for h in ps.heroes)
        ps.ultimates_earned = sum(h.ultimates_earned for h in ps.heroes)
        ps.ultimates_used = sum(h.ultimates_used for h in ps.heroes)
        ps.time_played = max((h.time_played for h in ps.heroes), default=0)
        tf = sum(h.shots_fired for h in ps.heroes)
        th = sum(h.shots_hit for h in ps.heroes)
        ps.weapon_accuracy = round(th / tf, 4) if tf > 0 else 0
        players.append(ps)

    round_stats = _compute_round_stats(rounds_data)

    parse_warnings = []
    if bad_lines > 0:
        parse_warnings.append(f"Skipped {bad_lines} malformed line(s) during parsing")

    return ParsedMatch(
        map_name=map_name, game_mode=game_mode,
        team1_label=team1_label, team2_label=team2_label,
        winner_label=winner_label, duration_seconds=duration_seconds,
        players=players, file_hash=file_hash, file_name=file_name,
        round_stats=round_stats, kills=kills,
        parse_warnings=parse_warnings,
    )