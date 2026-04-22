from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.models.match import Team, Encounter, Match, MatchPlayer, MatchPlayerHero, MatchKill
from app.models.user import User, BattleTag
from app.models.tournament import Tournament
from app.schemas.match import TeamCreate, EncounterCreate, PlayerMappingItem
from app.services.log_parser import parse_log
from app.services.match_metrics import compute_match_metrics, determine_first_bloods


class MatchService:

    @staticmethod
    async def create_team(db: AsyncSession, data: TeamCreate) -> Team:
        team = Team(
            tournament_id=data.tournament_id,
            name=data.name,
            captain_user_id=data.captain_user_id
        )
        db.add(team)
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def get_teams_by_tournament(db: AsyncSession, tournament_id: int) -> List[Team]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Team)
            .options(
                selectinload(Team.tournament_participants),
                selectinload(Team.captain),
            )
            .where(Team.tournament_id == tournament_id)
            .order_by(Team.name)
        )
        return result.scalars().all()

    @staticmethod
    async def create_encounter(db: AsyncSession, data: EncounterCreate) -> Encounter:
        encounter = Encounter(
            tournament_id=data.tournament_id,
            team1_id=data.team1_id,
            team2_id=data.team2_id,
            stage_name=data.stage,
            round_number=data.round_number
        )
        db.add(encounter)
        await db.commit()
        await db.refresh(encounter, attribute_names=[
            'id', 'tournament_id', 'team1_id', 'team2_id',
            'team1_score', 'team2_score', 'winner_team_id',
            'stage_name', 'round_number', 'is_auto_created', 'created_at'
        ])
        return encounter

    @staticmethod
    async def get_encounter(db: AsyncSession, encounter_id: int) -> Encounter:
        result = await db.execute(
            select(Encounter)
            .options(
                selectinload(Encounter.team1),
                selectinload(Encounter.team2),
                selectinload(Encounter.matches).options(
                    selectinload(Match.players).options(
                        selectinload(MatchPlayer.user),
                        selectinload(MatchPlayer.heroes)
                    )
                )
            )
            .where(Encounter.id == encounter_id)
        )
        encounter = result.scalar_one_or_none()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        return encounter

    @staticmethod
    async def get_encounters_by_tournament(db: AsyncSession, tournament_id: int) -> List[Encounter]:
        result = await db.execute(
            select(Encounter)
            .options(
                selectinload(Encounter.team1),
                selectinload(Encounter.team2),
                selectinload(Encounter.matches)
            )
            .where(Encounter.tournament_id == tournament_id)
            .order_by(Encounter.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_match(db: AsyncSession, match_id: int) -> Match:
        result = await db.execute(
            select(Match)
            .options(
                selectinload(Match.team1),
                selectinload(Match.team2),
                selectinload(Match.winner),
                selectinload(Match.players).options(
                    selectinload(MatchPlayer.user),
                    selectinload(MatchPlayer.heroes)
                )
            )
            .where(Match.id == match_id)
        )
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return match

    @staticmethod
    async def find_user_by_player_name(db: AsyncSession, player_name: str) -> List[User]:
        result = await db.execute(
            select(User)
            .join(BattleTag, BattleTag.user_id == User.id)
            .where(
                func.split_part(BattleTag.tag, '#', 1).ilike(player_name)
            )
        )
        return result.scalars().all()

    @staticmethod
    async def upload_log(
        db: AsyncSession,
        file_content: bytes,
        file_name: str,
        encounter_id: Optional[int],
        tournament_id: Optional[int],
        map_number: Optional[int],
        player_mappings: List[PlayerMappingItem]
    ) -> dict:
        parsed = parse_log(file_content, file_name)

        result = await db.execute(
            select(Match).where(Match.file_hash == parsed.file_hash)
        )
        if existing := result.scalar_one_or_none():
            return {'status': 'duplicate', 'match_id': existing.id}

        # === Гибридная система: если encounter_id не указан, ищем/создаём автоматически ===
        if encounter_id is None:
            if tournament_id is None:
                raise HTTPException(status_code=400, detail="Either encounter_id or tournament_id is required")

            # Ищем существующий encounter между командами
            # Определяем названия команд из лога
            log_team1_name = parsed.team1_label
            log_team2_name = parsed.team2_label

            # Ищем DB-команды по названиям из лога
            result = await db.execute(
                select(Team).where(
                    Team.tournament_id == tournament_id,
                    Team.name == log_team1_name
                )
            )
            db_team1 = result.scalar_one_or_none()

            result = await db.execute(
                select(Team).where(
                    Team.tournament_id == tournament_id,
                    Team.name == log_team2_name
                )
            )
            db_team2 = result.scalar_one_or_none()

            if db_team1 and db_team2:
                # Ищем существующий encounter между этими командами
                result = await db.execute(
                    select(Encounter).where(
                        Encounter.tournament_id == tournament_id,
                        (
                            (Encounter.team1_id == db_team1.id) & (Encounter.team2_id == db_team2.id)
                            | (Encounter.team1_id == db_team2.id) & (Encounter.team2_id == db_team1.id)
                        )
                    )
                )
                existing_encounters = result.scalars().all()

                if existing_encounters:
                    # Берём последний (самый свежий)
                    encounter = existing_encounters[-1]
                else:
                    # Создаём новый encounter автоматически
                    encounter = Encounter(
                        tournament_id=tournament_id,
                        team1_id=db_team1.id,
                        team2_id=db_team2.id,
                        is_auto_created=1,
                    )
                    db.add(encounter)
                    await db.flush()
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Teams not found: '{log_team1_name}' / '{log_team2_name}'. Создайте команды вручную."
                )
        else:
            result = await db.execute(
                select(Encounter)
                .options(
                    selectinload(Encounter.team1),
                    selectinload(Encounter.team2)
                )
                .where(Encounter.id == encounter_id)
            )
            encounter = result.scalar_one_or_none()
            if not encounter:
                raise HTTPException(status_code=404, detail="Encounter not found")

        manual_mapping: dict[str, Optional[int]] = {
            m.player_name: m.user_id for m in player_mappings
        }

        conflicts = []
        player_user_map: dict[str, Optional[int]] = {}
        unique_players = {p.player_name for p in parsed.players}

        for player_name in unique_players:
            if player_name in manual_mapping:
                player_user_map[player_name] = manual_mapping[player_name]
                continue
            found_users = await MatchService.find_user_by_player_name(db, player_name)
            if len(found_users) == 0:
                player_user_map[player_name] = None
            elif len(found_users) == 1:
                player_user_map[player_name] = found_users[0].id
            else:
                conflicts.append({
                    'player_name': player_name,
                    'candidates': [
                        {'user_id': u.id, 'username': u.username, 'discord_id': u.discord_id}
                        for u in found_users
                    ]
                })

        if conflicts:
            return {
                'status': 'ambiguous',
                'conflicts': conflicts,
                'parsed_map': parsed.map_name,
                'parsed_players': [p.player_name for p in parsed.players]
            }

        log_team1_player_names = {
            p.player_name.lower() for p in parsed.players
            if p.team_label == parsed.team1_label
        }

        log_team1_is_db_team1 = False
        if any(p_name in encounter.team1.name.lower() for p_name in log_team1_player_names):
            log_team1_is_db_team1 = True
        elif any(p_name in encounter.team2.name.lower() for p_name in log_team1_player_names):
            log_team1_is_db_team1 = False

        if log_team1_is_db_team1:
            log_to_db_map: Dict[str, Team] = {
                parsed.team1_label: encounter.team1,
                parsed.team2_label: encounter.team2,
            }
        else:
            log_to_db_map: Dict[str, Team] = {
                parsed.team1_label: encounter.team2,
                parsed.team2_label: encounter.team1,
            }

        winner_team_id = (
            log_to_db_map[parsed.winner_label].id
            if parsed.winner_label and parsed.winner_label in log_to_db_map
            else None
        )
        for round_data in parsed.round_stats:
            for player in round_data['players']:
                team_obj = log_to_db_map.get(player['team_label'])
                player['team_id'] = team_obj.id if team_obj else None

        match = Match(
            encounter_id=encounter.id,
            tournament_id=encounter.tournament_id,
            team1_id=encounter.team1_id,
            team2_id=encounter.team2_id,
            winner_team_id=winner_team_id,
            map_name=parsed.map_name,
            game_mode=parsed.game_mode,
            duration_seconds=parsed.duration_seconds,
            file_hash=parsed.file_hash,
            file_name=parsed.file_name,
            map_number=map_number,
            round_stats=parsed.round_stats,
        )

        db.add(match)
        await db.flush()

        # Создаём промежуточные объекты MatchPlayer без метрик
        match_player_objects: List[MatchPlayer] = []
        players_metrics_data: List[Dict] = []

        for player_stat in parsed.players:
            user_id = player_user_map.get(player_stat.player_name)
            team_id = (
                log_to_db_map[player_stat.team_label].id
                if player_stat.team_label in log_to_db_map
                else None
            )

            match_player = MatchPlayer(
                match_id=match.id,
                user_id=user_id,
                player_name=player_stat.player_name,
                team_label=player_stat.team_label,
                team_id=team_id,
                eliminations=player_stat.eliminations,
                final_blows=player_stat.final_blows,
                deaths=player_stat.deaths,
                all_damage_dealt=player_stat.all_damage_dealt,
                hero_damage_dealt=player_stat.hero_damage_dealt,
                healing_dealt=player_stat.healing_dealt,
                healing_received=player_stat.healing_received,
                self_healing=player_stat.self_healing,
                damage_taken=player_stat.damage_taken,
                damage_blocked=player_stat.damage_blocked,
                defensive_assists=player_stat.defensive_assists,
                offensive_assists=player_stat.offensive_assists,
                objective_kills=player_stat.objective_kills,
                ultimates_earned=player_stat.ultimates_earned,
                ultimates_used=player_stat.ultimates_used,
                time_played=player_stat.time_played,
            )
            db.add(match_player)
            await db.flush()
            match_player_objects.append(match_player)

            # Данные для расчёта метрик
            players_metrics_data.append({
                'match_player_obj': match_player,
                'team_id': team_id,
                'eliminations': player_stat.eliminations,
                'final_blows': player_stat.final_blows,
                'deaths': player_stat.deaths,
                'hero_damage_dealt': player_stat.hero_damage_dealt,
                'healing_dealt': player_stat.healing_dealt,
                'damage_blocked': player_stat.damage_blocked,
                'offensive_assists': player_stat.offensive_assists,
                'defensive_assists': player_stat.defensive_assists,
                'heroes': player_stat.heroes,
            })

            for hero_stat in player_stat.heroes:
                match_player_hero = MatchPlayerHero(
                    match_player_id=match_player.id,
                    hero_name=hero_stat.hero_name,
                    eliminations=hero_stat.eliminations,
                    final_blows=hero_stat.final_blows,
                    deaths=hero_stat.deaths,
                    all_damage_dealt=hero_stat.all_damage_dealt,
                    barrier_damage_dealt=hero_stat.barrier_damage_dealt,
                    hero_damage_dealt=hero_stat.hero_damage_dealt,
                    healing_dealt=hero_stat.healing_dealt,
                    healing_received=hero_stat.healing_received,
                    self_healing=hero_stat.self_healing,
                    damage_taken=hero_stat.damage_taken,
                    damage_blocked=hero_stat.damage_blocked,
                    defensive_assists=hero_stat.defensive_assists,
                    offensive_assists=hero_stat.offensive_assists,
                    objective_kills=hero_stat.objective_kills,
                    ultimates_earned=hero_stat.ultimates_earned,
                    ultimates_used=hero_stat.ultimates_used,
                    multikill_best=hero_stat.multikill_best,
                    multikills=hero_stat.multikills,
                    solo_kills=hero_stat.solo_kills,
                    environmental_kills=hero_stat.environmental_kills,
                    environmental_deaths=hero_stat.environmental_deaths,
                    critical_hits=hero_stat.critical_hits,
                    critical_hit_accuracy=hero_stat.critical_hit_accuracy,
                    scoped_accuracy=hero_stat.scoped_accuracy,
                    scoped_critical_hit_accuracy=hero_stat.scoped_critical_hit_accuracy,
                    scoped_critical_hit_kills=hero_stat.scoped_critical_hit_kills,
                    shots_fired=hero_stat.shots_fired,
                    shots_hit=hero_stat.shots_hit,
                    shots_missed=hero_stat.shots_missed,
                    scoped_shots_fired=hero_stat.scoped_shots_fired,
                    scoped_shots_hit=hero_stat.scoped_shots_hit,
                    weapon_accuracy=hero_stat.weapon_accuracy,
                    time_played=hero_stat.time_played,
                )
                db.add(match_player_hero)

        # Сохранение Kill Feed
        for kill in parsed.kills:
            killer_user_id = player_user_map.get(kill.killer_name)
            victim_user_id = player_user_map.get(kill.victim_name)

            match_kill = MatchKill(
                match_id=match.id,
                killer_name=kill.killer_name,
                killer_team_label=kill.killer_team_label,
                killer_hero=kill.killer_hero,
                killer_user_id=killer_user_id,
                victim_name=kill.victim_name,
                victim_team_label=kill.victim_team_label,
                victim_hero=kill.victim_hero,
                victim_user_id=victim_user_id,
                weapon=kill.weapon,
                damage=kill.damage,
                is_critical=int(kill.is_critical),
                is_headshot=int(kill.is_headshot),
                timestamp=kill.timestamp,
                round_number=kill.round_number,
                offensive_assists=[
                    {'player_name': a.player_name, 'team_label': a.team_label, 'hero_name': a.hero_name}
                    for a in kill.offensive_assists
                ] if kill.offensive_assists else None,
                defensive_assists=[
                    {'player_name': a.player_name, 'team_label': a.team_label, 'hero_name': a.hero_name}
                    for a in kill.defensive_assists
                ] if kill.defensive_assists else None,
            )
            db.add(match_kill)

        # === First Blood: определяем первый килл каждого раунда ===
        all_kills_result = await db.execute(
            select(MatchKill)
            .where(MatchKill.match_id == match.id)
            .order_by(MatchKill.round_number, MatchKill.timestamp)
        )
        all_kills = all_kills_result.scalars().all()
        first_blood_map = determine_first_bloods(all_kills)

        for kill in all_kills:
            if kill.id in first_blood_map.values() and first_blood_map.get(kill.round_number) == kill.id:
                kill.is_first_blood = 1

        # === Contribution Score, MVP/SVP, last_hero ===
        compute_match_metrics(players_metrics_data, winner_team_id)

        # Обновляем MatchPlayer объекты рассчитанными метриками
        for pdata in players_metrics_data:
            mp = pdata['match_player_obj']
            mp.contribution_score = pdata['contribution_score']
            mp.is_mvp = pdata['is_mvp']
            mp.is_svp = pdata['is_svp']
            mp.last_hero = pdata['last_hero']

        if winner_team_id == encounter.team1_id:
            encounter.team1_score += 1
        elif winner_team_id == encounter.team2_id:
            encounter.team2_score += 1

        if encounter.team1_score > encounter.team2_score:
            encounter.winner_team_id = encounter.team1_id
        elif encounter.team2_score > encounter.team1_score:
            encounter.winner_team_id = encounter.team2_id

        await db.commit()

        result = {'status': 'ok', 'match_id': match.id}
        if parsed.parse_warnings:
            result['warnings'] = parsed.parse_warnings

        return result

    @staticmethod
    async def get_player_match_history(db: AsyncSession, user_id: int) -> List[dict]:
        result = await db.execute(
            select(MatchPlayer)
            .options(
                selectinload(MatchPlayer.match).options(
                    selectinload(Match.encounter).options(
                        selectinload(Encounter.team1),
                        selectinload(Encounter.team2),
                    ),
                    selectinload(Match.team1),
                    selectinload(Match.team2),
                ),
                selectinload(MatchPlayer.heroes)
            )
            .where(MatchPlayer.user_id == user_id)
            .order_by(MatchPlayer.created_at.desc())
        )
        match_players = result.scalars().all()

        history = []
        for mp in match_players:
            match = mp.match
            if not match or not match.encounter:
                continue
            encounter = match.encounter
            tourney_result = await db.execute(
                select(Tournament).where(Tournament.id == match.tournament_id)
            )
            tournament = tourney_result.scalar_one_or_none()
            history.append({
                'match_id': match.id,
                'encounter_id': encounter.id,
                'tournament_id': match.tournament_id,
                'tournament_name': tournament.title if tournament else 'Unknown',
                'map_name': match.map_name,
                'stage': encounter.stage,
                'team1_name': encounter.team1.name if encounter.team1 else 'Team 1',
                'team2_name': encounter.team2.name if encounter.team2 else 'Team 2',
                'team1_score': encounter.team1_score,
                'team2_score': encounter.team2_score,
                'eliminations': mp.eliminations,
                'final_blows': mp.final_blows,
                'deaths': mp.deaths,
                'hero_damage_dealt': mp.hero_damage_dealt,
                'healing_dealt': mp.healing_dealt,
                'damage_blocked': mp.damage_blocked,
                'objective_kills': mp.objective_kills,
                'heroes': [h.hero_name for h in mp.heroes]
            })

        return history

    @staticmethod
    async def get_match_killfeed(db: AsyncSession, match_id: int) -> List[dict]:
        result = await db.execute(
            select(MatchKill)
            .where(MatchKill.match_id == match_id)
            .order_by(MatchKill.timestamp)
        )
        kills = result.scalars().all()
        return [
            {
                'id': k.id,
                'killer_name': k.killer_name,
                'killer_team_label': k.killer_team_label,
                'killer_hero': k.killer_hero,
                'killer_user_id': k.killer_user_id,
                'victim_name': k.victim_name,
                'victim_team_label': k.victim_team_label,
                'victim_hero': k.victim_hero,
                'victim_user_id': k.victim_user_id,
                'weapon': k.weapon,
                'damage': k.damage,
                'is_critical': bool(k.is_critical),
                'is_headshot': bool(k.is_headshot),
                'is_first_blood': bool(k.is_first_blood),
                'timestamp': k.timestamp,
                'round_number': k.round_number,
                'offensive_assists': k.offensive_assists or [],
                'defensive_assists': k.defensive_assists or [],
            }
            for k in kills
        ]

    @staticmethod
    async def delete_match(db: AsyncSession, match_id: int) -> dict:
        result = await db.execute(select(Match).where(Match.id == match_id))
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        await db.delete(match)
        await db.commit()
        return {'status': 'ok'}

    @staticmethod
    async def get_match_first_blood(db: AsyncSession, match_id: int) -> List[dict]:
        """Возвращает first blood kills для каждого раунда матча."""
        result = await db.execute(
            select(MatchKill)
            .where(
                MatchKill.match_id == match_id,
                MatchKill.is_first_blood == 1
            )
            .order_by(MatchKill.round_number)
        )
        kills = result.scalars().all()
        return [
            {
                'round_number': k.round_number,
                'killer_name': k.killer_name,
                'killer_team_label': k.killer_team_label,
                'killer_hero': k.killer_hero,
                'killer_user_id': k.killer_user_id,
                'victim_name': k.victim_name,
                'victim_team_label': k.victim_team_label,
                'victim_hero': k.victim_hero,
                'victim_user_id': k.victim_user_id,
                'weapon': k.weapon,
                'timestamp': k.timestamp,
            }
            for k in kills
        ]

    # ============================
    # ADMIN: Encounter Result
    # ============================
    @staticmethod
    async def update_encounter_result(
        db: AsyncSession,
        encounter_id: int,
        team1_score: Optional[int] = None,
        team2_score: Optional[int] = None,
        winner_team_id: Optional[int] = None,
    ) -> dict:
        """Обновить счёт encounter и определить победителя."""
        result = await db.execute(
            select(Encounter).where(Encounter.id == encounter_id)
        )
        encounter = result.scalar_one_or_none()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        if team1_score is not None:
            encounter.team1_score = team1_score
        if team2_score is not None:
            encounter.team2_score = team2_score
        if winner_team_id is not None:
            encounter.winner_team_id = winner_team_id
        elif team1_score is not None and team2_score is not None:
            if team1_score > team2_score:
                encounter.winner_team_id = encounter.team1_id
            elif team2_score > team1_score:
                encounter.winner_team_id = encounter.team2_id

        await db.commit()
        await db.refresh(encounter)
        return MatchService._encounter_to_dict(encounter)

    @staticmethod
    async def set_encounter_forfeit(
        db: AsyncSession,
        encounter_id: int,
        loser_team_id: int,
    ) -> dict:
        """Засчитать техническое поражение."""
        result = await db.execute(
            select(Encounter).where(Encounter.id == encounter_id)
        )
        encounter = result.scalar_one_or_none()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        if loser_team_id not in (encounter.team1_id, encounter.team2_id):
            raise HTTPException(status_code=400, detail="Team is not part of this encounter")

        winner_id = encounter.team2_id if loser_team_id == encounter.team1_id else encounter.team1_id
        encounter.winner_team_id = winner_id

        await db.commit()
        await db.refresh(encounter)
        return MatchService._encounter_to_dict(encounter)

    # ============================
    # SWISS SYSTEM
    # ============================
    @staticmethod
    async def generate_swiss_next_round(
        db: AsyncSession,
        tournament_id: int,
        avoid_repeat: bool = True,
    ) -> dict:
        """Генерирует пары для следующего тура швейцарской системы."""
        tournament = await db.get(Tournament, tournament_id)
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        teams_result = await db.execute(
            select(Team).where(Team.tournament_id == tournament_id)
        )
        teams = teams_result.scalars().all()
        if not teams:
            raise HTTPException(status_code=400, detail="No teams in this tournament")

        enc_result = await db.execute(
            select(Encounter).where(
                Encounter.tournament_id == tournament_id,
                Encounter.winner_team_id != None
            )
        )
        completed = enc_result.scalars().all()

        team_wins = {t.id: 0 for t in teams}
        played_pairs = set()

        for enc in completed:
            if enc.winner_team_id:
                team_wins[enc.winner_team_id] = team_wins.get(enc.winner_team_id, 0) + 1
            played_pairs.add(frozenset({enc.team1_id, enc.team2_id}))

        max_round = max((e.round_number for e in completed), default=0)
        next_round = max_round + 1

        from collections import defaultdict
        score_groups = defaultdict(list)
        for team in teams:
            score_groups[team_wins[team.id]].append(team.id)

        new_encounters = []
        used_teams = set()

        for score in sorted(score_groups.keys(), reverse=True):
            team_ids = [tid for tid in score_groups[score] if tid not in used_teams]
            import random
            random.shuffle(team_ids)

            for i in range(0, len(team_ids) - 1, 2):
                t1, t2 = team_ids[i], team_ids[i + 1]
                pair = frozenset({t1, t2})

                if avoid_repeat and pair in played_pairs:
                    swapped = False
                    for j in range(i + 2, len(team_ids)):
                        alt = team_ids[j]
                        if alt in used_teams:
                            continue
                        alt_pair1 = frozenset({t1, alt})
                        if alt_pair1 not in played_pairs:
                            new_encounters.append({'team1_id': t1, 'team2_id': alt, 'round_number': next_round, 'score_group': score})
                            used_teams.add(t1)
                            used_teams.add(alt)
                            swapped = True
                            break
                    if not swapped:
                        new_encounters.append({'team1_id': t1, 'team2_id': t2, 'round_number': next_round, 'score_group': score})
                        used_teams.add(t1)
                        used_teams.add(t2)
                else:
                    new_encounters.append({'team1_id': t1, 'team2_id': t2, 'round_number': next_round, 'score_group': score})
                    used_teams.add(t1)
                    used_teams.add(t2)

        bye_teams = [t.id for t in teams if t.id not in used_teams]

        created = []
        for enc_data in new_encounters:
            encounter = Encounter(
                tournament_id=tournament_id,
                team1_id=enc_data['team1_id'],
                team2_id=enc_data['team2_id'],
                round_number=enc_data['round_number'],
                stage=f"Swiss Round {enc_data['round_number']}",
                is_auto_created=1,
            )
            db.add(encounter)
            await db.flush()
            await db.refresh(encounter)
            created.append(MatchService._encounter_to_dict(encounter))

        await db.commit()
        return {'round': next_round, 'encounters': created, 'bye_teams': bye_teams, 'message': f"Created {len(created)} encounters for round {next_round}"}

    # ============================
    # ADMIN: Report Encounter Result (Single-Elimination Auto-Advance)
    # ============================
    @staticmethod
    async def report_encounter_result(
        db: AsyncSession,
        encounter_id: int,
        team1_score: int,
        team2_score: int,
    ) -> dict:
        """
        Сообщить результат встречи, определить победителя и продвинуть его
        в следующий раунд single-elimination сетки.

        Логика (в одной транзакции):
        1. Найти encounter по id, проверить что не completed
        2. Определить победителя по счёту (ничья = ошибка 400)
        3. Обновить счёт и победителя
        4. Если есть next_encounter_id — продвинуть победителя в следующий матч
        5. await db.commit()

        Args:
            db: сессия БД
            encounter_id: ID встречи
            team1_score: счёт первой команды
            team2_score: счёт второй команды

        Returns:
            dict с данными обновлённого encounter

        Raises:
            HTTPException 404 — encounter не найден
            HTTPException 409 — encounter уже завершён
            HTTPException 400 — ничья (score cannot be a draw)
        """
        from sqlalchemy.orm import selectinload

        # 1. Находим encounter
        result = await db.execute(
            select(Encounter)
            .options(
                selectinload(Encounter.team1),
                selectinload(Encounter.team2),
                selectinload(Encounter.next_encounter),
            )
            .where(Encounter.id == encounter_id)
        )
        encounter = result.scalar_one_or_none()

        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        # 2. Проверяем что encounter ещё не завершён
        if encounter.winner_team_id is not None:
            raise HTTPException(
                status_code=409,
                detail="Encounter already completed"
            )

        # 3. Проверяем что обе команды на месте
        if not encounter.team1_id or not encounter.team2_id:
            raise HTTPException(
                status_code=400,
                detail="Both teams must be present to report result"
            )

        # 4. Определяем победителя (ничья недопустима)
        if team1_score == team2_score:
            raise HTTPException(
                status_code=400,
                detail="Score cannot be a draw in single-elimination"
            )

        winner_id = encounter.team1_id if team1_score > team2_score else encounter.team2_id

        # 5. Обновляем счёт и победителя
        encounter.team1_score = team1_score
        encounter.team2_score = team2_score
        encounter.winner_team_id = winner_id

        # 6. Продвижение победителя в следующий матч
        if encounter.next_encounter_id is not None:
            next_enc = encounter.next_encounter

            # Определяем в какой слот поместить победителя.
            # Если team1_id пустой — заполняем его, иначе team2_id.
            if next_enc.team1_id is None:
                next_enc.team1_id = winner_id
            elif next_enc.team2_id is None:
                next_enc.team2_id = winner_id
            else:
                # Оба слота уже заполнены — ошибка конфигурации сетки
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Both slots filled in next encounter {next_enc.id} "
                    f"(teams: {next_enc.team1_id}, {next_enc.team2_id}). "
                    f"Winner {winner_id} from encounter {encounter_id} has nowhere to advance."
                )

        await db.commit()
        await db.refresh(encounter)

        return MatchService._encounter_to_dict(encounter)

    @staticmethod
    def _encounter_to_dict(enc: Encounter) -> dict:
        return {
            'id': enc.id,
            'tournament_id': enc.tournament_id,
            'team1_id': enc.team1_id,
            'team2_id': enc.team2_id,
            'team1_score': enc.team1_score,
            'team2_score': enc.team2_score,
            'winner_team_id': enc.winner_team_id,
            'stage': enc.stage_name,
            'round_number': enc.round_number,
            'is_auto_created': enc.is_auto_created,
            'next_encounter_id': enc.next_encounter_id,
            'created_at': enc.created_at.isoformat() if enc.created_at else None,
        }