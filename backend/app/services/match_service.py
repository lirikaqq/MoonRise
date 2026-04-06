from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import Optional, List, Dict

from app.models.match import Team, Encounter, Match, MatchPlayer, MatchPlayerHero
from app.models.user import User, BattleTag
from app.models.tournament import Tournament
from app.schemas.match import TeamCreate, EncounterCreate, PlayerMappingItem
from app.services.log_parser import parse_log


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
        result = await db.execute(
            select(Team)
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
            stage=data.stage,
            round_number=data.round_number
        )
        db.add(encounter)
        await db.commit()
        await db.refresh(encounter)
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
        encounter_id: int,
        map_number: Optional[int],
        player_mappings: List[PlayerMappingItem]
    ) -> dict:
        parsed = parse_log(file_content, file_name)

        result = await db.execute(
            select(Match).where(Match.file_hash == parsed.file_hash)
        )
        if existing := result.scalar_one_or_none():
            return {'status': 'duplicate', 'match_id': existing.id}

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

        if winner_team_id == encounter.team1_id:
            encounter.team1_score += 1
        elif winner_team_id == encounter.team2_id:
            encounter.team2_score += 1

        if encounter.team1_score > encounter.team2_score:
            encounter.winner_team_id = encounter.team1_id
        elif encounter.team2_score > encounter.team1_score:
            encounter.winner_team_id = encounter.team2_id

        await db.commit()

        return {'status': 'ok', 'match_id': match.id}

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
    async def delete_match(db: AsyncSession, match_id: int) -> dict:
        result = await db.execute(select(Match).where(Match.id == match_id))
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        await db.delete(match)
        await db.commit()
        return {'status': 'ok'}