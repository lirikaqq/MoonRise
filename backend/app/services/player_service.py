from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, distinct
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict
from datetime import datetime, timezone
from collections import defaultdict

from app.models.user import User
from app.models.tournament import Tournament, TournamentParticipant
from app.models.match import MatchPlayer, MatchPlayerHero, Match, Encounter
from app.schemas.player import PlayerUpdate


class PlayerService:

    @staticmethod
    async def get_all_players(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User)
            .order_by(User.username)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_player_profile(db: AsyncSession, player_id: int) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(selectinload(User.battletags))
            .where(User.id == player_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_player_tournaments(db: AsyncSession, player_id: int) -> list:
        # Убедимся, что игрок существует
        player = await db.get(User, player_id)
        if not player:
            return []

        result = await db.execute(
            select(Tournament, TournamentParticipant)
            .join(TournamentParticipant, Tournament.id == TournamentParticipant.tournament_id)
            .where(TournamentParticipant.user_id == player_id)
            .order_by(Tournament.start_date.desc())
        )
        
        tournaments_data = []
        for tournament, participant in result.all():
            tournaments_data.append({
                "tournament_id": tournament.id,
                "title": tournament.title,
                "format": tournament.format,
                "status": tournament.status,
                "start_date": tournament.start_date.isoformat(),
                "cover_url": tournament.cover_url,
                "participant_status": participant.status,
                "is_allowed": participant.is_allowed,
                "checked_in": bool(participant.checkedin_at)
            })
        return tournaments_data
    
    @staticmethod
    async def update_player(db: AsyncSession, user_id: int, data: PlayerUpdate) -> User:
        user = await db.get(User, user_id)
        if not user:
            return None # Обработка в роутере
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user

    # 👇 НОВЫЙ МЕТОД 👇
    @staticmethod
    async def delete_player(db: AsyncSession, player_id: int) -> Optional[User]:
        """Полностью удаляет игрока и всю связанную с ним статистику."""
        player = await db.get(User, player_id)
        if not player:
            return None

        # Шаг 1: Удаляем статистику по героям игрока во всех матчах.
        # Это нужно делать вручную, т.к. прямой связи с User нет (через MatchPlayer).
        await db.execute(
            delete(MatchPlayerHero).where(
                MatchPlayerHero.match_player_id.in_(
                    select(MatchPlayer.id).where(MatchPlayer.user_id == player_id)
                )
            )
        )

        # Шаг 2: Удаляем статистику игрока во всех матчах.
        # Это нужно делать вручную, т.к. в модели User->MatchPlayer стоит ondelete="SET NULL".
        await db.execute(
            delete(MatchPlayer).where(MatchPlayer.user_id == player_id)
        )
        
        # Шаг 3: Удаляем самого игрока.
        # SQLAlchemy благодаря cascade='all, delete-orphan' и ondelete='CASCADE' 
        # в моделях User и Tournament позаботится об остальном 
        # (BattleTags, TournamentParticipant и т.д.).
        await db.delete(player)
        await db.commit()
        return player

    # ============================================================
    # НОВЫЕ МЕТОДЫ ДЛЯ АГРЕГИРОВАННОЙ СТАТИСТИКИ
    # ============================================================

    @staticmethod
    async def get_player_profile_stats(db: AsyncSession, user_id: int) -> Optional[Dict]:
        """Агрегированная статистика игрока по всем матчам."""
        # Загружаем все MatchPlayer для игрока
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
                )
            )
            .where(MatchPlayer.user_id == user_id)
        )
        match_players = result.scalars().all()

        if not match_players:
            return None

        # Агрегация
        total_matches = len({mp.match_id for mp in match_players})
        total_elims = sum(mp.eliminations for mp in match_players)
        total_deaths = sum(mp.deaths for mp in match_players)
        total_assists = sum(mp.offensive_assists + mp.defensive_assists for mp in match_players)
        total_damage = sum(mp.hero_damage_dealt for mp in match_players)
        total_healing = sum(mp.healing_dealt for mp in match_players)
        total_time = sum(mp.time_played for mp in match_players)
        mvp_count = sum(1 for mp in match_players if mp.is_mvp)
        svp_count = sum(1 for mp in match_players if mp.is_svp)

        # Wins / losses через encounter
        wins = 0
        losses = 0
        unique_maps = set()
        for mp in match_players:
            match = mp.match
            if not match or not match.encounter:
                continue
            encounter = match.encounter
            unique_maps.add(match.map_name)

            # Определяем, выиграл ли игрок
            player_team_id = mp.team_id
            if player_team_id and encounter.winner_team_id:
                if player_team_id == encounter.winner_team_id:
                    wins += 1
                else:
                    losses += 1

        total_decisive = wins + losses
        if total_decisive == 0:
            # Если нет данных о победах — считаем все матчи как total
            losses = total_matches
            total_decisive = total_matches

        winrate = (wins / max(total_decisive, 1)) * 100
        kda = (total_elims + total_assists) / max(total_deaths, 1)

        return {
            "total_matches": total_matches,
            "wins": wins,
            "losses": losses,
            "winrate": round(winrate, 1),
            "kda_ratio": round(kda, 2),
            "elims_avg": round(total_elims / max(total_matches, 1), 2),
            "deaths_avg": round(total_deaths / max(total_matches, 1), 2),
            "assists_avg": round(total_assists / max(total_matches, 1), 2),
            "damage_avg": round(total_damage / max(total_matches, 1), 2),
            "healing_avg": round(total_healing / max(total_matches, 1), 2),
            "mvp_count": mvp_count,
            "svp_count": svp_count,
            "playtime_hours": round(total_time / 3600, 1),
            "maps_count": len(unique_maps),
        }

    @staticmethod
    async def get_player_top_heroes(db: AsyncSession, user_id: int, limit: int = 5) -> List[Dict]:
        """Топ героев игрока по времени игры."""
        result = await db.execute(
            select(MatchPlayerHero, MatchPlayer.match_id)
            .join(MatchPlayer, MatchPlayerHero.match_player_id == MatchPlayer.id)
            .where(MatchPlayer.user_id == user_id)
        )
        rows = result.all()

        if not rows:
            return []

        # Группировка по hero_name
        hero_stats: Dict[str, Dict] = defaultdict(lambda: {
            "time_played": 0,
            "eliminations": 0,
            "deaths": 0,
            "hero_damage_dealt": 0,
            "healing_dealt": 0,
            "match_ids": set(),
        })

        for hero, match_id in rows:
            h = hero_stats[hero.hero_name]
            h["time_played"] += hero.time_played or 0
            h["eliminations"] += hero.eliminations or 0
            h["deaths"] += hero.deaths or 0
            h["hero_damage_dealt"] += hero.hero_damage_dealt or 0
            h["healing_dealt"] += hero.healing_dealt or 0
            h["match_ids"].add(match_id)

        # Сортировка по time_played DESC
        sorted_heroes = sorted(
            hero_stats.items(),
            key=lambda x: x[1]["time_played"],
            reverse=True
        )[:limit]

        return [
            {
                "hero_name": name,
                "time_played": int(stats["time_played"]),
                "matches_played": len(stats["match_ids"]),
                "eliminations": stats["eliminations"],
                "deaths": stats["deaths"],
                "hero_damage_dealt": round(stats["hero_damage_dealt"], 2),
                "healing_dealt": round(stats["healing_dealt"], 2),
                "kda": round(
                    stats["eliminations"] / max(stats["deaths"], 1), 2
                ),
            }
            for name, stats in sorted_heroes
        ]

    @staticmethod
    async def get_player_enhanced_match_history(db: AsyncSession, user_id: int) -> List[Dict]:
        """Расширенная история матчей с result, kda, mvp/svp, main_hero."""
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

            # Определяем результат
            player_team_id = mp.team_id
            if player_team_id and encounter.winner_team_id:
                result_str = "win" if player_team_id == encounter.winner_team_id else "loss"
            else:
                result_str = "unknown"

            # KDA за матч
            assists = mp.offensive_assists + mp.defensive_assists
            kda = (mp.eliminations + assists) / max(mp.deaths, 1)

            # Главный герой (максимальное время)
            main_hero = None
            if mp.heroes:
                main_hero = max(mp.heroes, key=lambda h: h.time_played).hero_name

            history.append({
                "match_id": match.id,
                "encounter_id": encounter.id,
                "tournament_id": match.tournament_id,
                "tournament_name": tournament.title if tournament else "Unknown",
                "map_name": match.map_name,
                "stage": encounter.stage_name,
                "team1_name": encounter.team1.name if encounter.team1 else "Team 1",
                "team2_name": encounter.team2.name if encounter.team2 else "Team 2",
                "team1_score": encounter.team1_score,
                "team2_score": encounter.team2_score,
                "result": result_str,
                "eliminations": mp.eliminations,
                "final_blows": mp.final_blows,
                "deaths": mp.deaths,
                "hero_damage_dealt": mp.hero_damage_dealt,
                "healing_dealt": mp.healing_dealt,
                "damage_blocked": mp.damage_blocked,
                "objective_kills": mp.objective_kills,
                "kda": round(kda, 2),
                "is_mvp": bool(mp.is_mvp),
                "is_svp": bool(mp.is_svp),
                "main_hero": main_hero,
                "heroes": [h.hero_name for h in mp.heroes],
            })

        return history