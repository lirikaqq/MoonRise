"""
Расчёт метрик матча: Contribution Score, MVP/SVP, First Blood, last_hero.

Contribution Score формула (адаптирована из anak-tournaments PerformancePoints):
  CS = elim*500 + fb*250 + assists*50 + hero_dmg + healing - deaths*750 + blocked*0.1

MVP — игрок победившей команды с максимальным contribution_score.
SVP — игрок проигравшей команды с максимальным contribution_score.

First Blood — первый kill в каждом раунде (минимальный timestamp среди kills раунда).

last_hero — герой с максимальным time_played у игрока.
"""

from typing import List, Dict, Optional, Any
from app.models.match import MatchKill


def calculate_contribution_score(
    eliminations: int,
    final_blows: int,
    deaths: int,
    hero_damage_dealt: float,
    healing_dealt: float,
    damage_blocked: float,
    offensive_assists: int,
    defensive_assists: int,
) -> float:
    """
    Рассчитывает Contribution Score игрока.
    Формула:
      CS = elim*500 + fb*250 + assists*50 + hero_dmg + healing - deaths*750 + blocked*0.1
    """
    assists = offensive_assists + defensive_assists
    score = (
        eliminations * 500
        + final_blows * 250
        + assists * 50
        + hero_damage_dealt
        + healing_dealt
        - deaths * 750
        + damage_blocked * 0.1
    )
    return round(score, 2)


def assign_mvp_svp(players_data: List[Dict[str, Any]], winner_team_id: Optional[int]) -> None:
    """
    Назначает is_mvp / is_svp игрокам.
    players_data — список dict-ов с полями: team_id, contribution_score, is_mvp, is_svp.
    Метод мутирует списки напрямую.
    """
    if not winner_team_id:
        return

    # Разделяем на победителей и проигравших
    winners = [p for p in players_data if p.get('team_id') == winner_team_id]
    losers = [p for p in players_data if p.get('team_id') != winner_team_id]

    # MVP: лучший среди победителей
    if winners:
        mvp = max(winners, key=lambda p: p.get('contribution_score', 0))
        mvp['is_mvp'] = 1

    # SVP: лучший среди проигравших
    if losers:
        svp = max(losers, key=lambda p: p.get('contribution_score', 0))
        svp['is_svp'] = 1


def determine_first_bloods(kills: List[MatchKill]) -> Dict[int, int]:
    """
    Определяет first blood для каждого раунда.
    Возвращает dict: round_number -> kill_id (первого килла раунда).
    """
    first_bloods: Dict[int, int] = {}

    for kill in kills:
        rnd = kill.round_number
        if rnd not in first_bloods or kill.timestamp < first_bloods[rnd]['timestamp']:
            first_bloods[rnd] = {
                'kill_id': kill.id,
                'timestamp': kill.timestamp,
            }

    return {rnd: data['kill_id'] for rnd, data in first_bloods.items()}


def get_last_hero(heroes: list) -> Optional[str]:
    """
    Возвращает имя героя с максимальным time_played.
    heroes — список MatchPlayerHero.
    """
    if not heroes:
        return None
    return max(heroes, key=lambda h: h.time_played).hero_name


def compute_match_metrics(
    players_data: List[Dict[str, Any]],
    winner_team_id: Optional[int],
) -> List[Dict[str, Any]]:
    """
    Полный пайплайн расчёта метрик для всех игроков матча.

    players_data — список dict, каждый с полями:
      eliminations, final_blows, deaths, hero_damage_dealt, healing_dealt,
      damage_blocked, offensive_assists, defensive_assists, team_id, heroes

    Возвращает тот же список, но с добавленными:
      contribution_score, is_mvp, is_svp, last_hero
    """
    for p in players_data:
        p['contribution_score'] = calculate_contribution_score(
            eliminations=p.get('eliminations', 0),
            final_blows=p.get('final_blows', 0),
            deaths=p.get('deaths', 0),
            hero_damage_dealt=p.get('hero_damage_dealt', 0),
            healing_dealt=p.get('healing_dealt', 0),
            damage_blocked=p.get('damage_blocked', 0),
            offensive_assists=p.get('offensive_assists', 0),
            defensive_assists=p.get('defensive_assists', 0),
        )
        p['last_hero'] = get_last_hero(p.get('heroes', []))
        p['is_mvp'] = 0
        p['is_svp'] = 0

    assign_mvp_svp(players_data, winner_team_id)
    return players_data
