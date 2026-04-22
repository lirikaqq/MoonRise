"""
Сервис для управления этапами турниров.
Генерация матчей для различных форматов, продвижение между этапами.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from app.models.tournament_stage import TournamentStage, StageGroup, StageFormat, SeedingRule
from app.models.match import Encounter, Team
from app.models.tournament import TournamentParticipant
from app.models.draft import DraftSession
from fastapi import HTTPException
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
import logging
from itertools import combinations

logger = logging.getLogger(__name__)


class StageService:
    """Сервис для работы с этапами турнира."""

    # ============================================================
    # ГЕНЕРАЦИЯ МАТЧЕЙ ДЛЯ РАЗЛИЧНЫХ ФОРМАТОВ
    # ============================================================

    @staticmethod
    async def generate_stage_matches(db: AsyncSession, stage_id: int) -> List[Encounter]:
        """
        Генерирует матчи для этапа на основе его формата.
        Поддерживаемые форматы:
        - ROUND_ROBIN: каждый с каждым внутри группы
        - SWISS: швейцарская система
        - SINGLE_ELIMINATION: одиночная сетка
        - DOUBLE_ELIMINATION: двойная сетка
        """
        stage_result = await db.execute(
            select(TournamentStage)
            .options(joinedload(TournamentStage.groups))
            .where(TournamentStage.id == stage_id)
        )
        stage = stage_result.scalar_one_or_none()

        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        if stage.format == StageFormat.ROUND_ROBIN:
            return await StageService._generate_round_robin(db, stage)
        elif stage.format == StageFormat.SWISS:
            return await StageService._generate_swiss(db, stage)
        elif stage.format == StageFormat.SINGLE_ELIMINATION:
            return await StageService._generate_single_elimination(db, stage)
        elif stage.format == StageFormat.DOUBLE_ELIMINATION:
            return await StageService._generate_double_elimination(db, stage)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported stage format: {stage.format}")

    @staticmethod
    async def _generate_round_robin(db: AsyncSession, stage: TournamentStage) -> List[Encounter]:
        """
        Round Robin: каждый играет с каждым внутри своей группы.
        Поддерживает неравномерные группы.
        """
        encounters = []

        # Получаем все группы этапа
        groups_result = await db.execute(
            select(StageGroup)
            .where(StageGroup.stage_id == stage.id)
            .order_by(StageGroup.name)
        )
        groups = groups_result.scalars().all()

        if not groups:
            raise HTTPException(status_code=400, detail="No groups found for round robin stage")

        for group in groups:
            # Получаем участников группы
            participants_result = await db.execute(
                select(TournamentParticipant)
                .where(TournamentParticipant.group_id == group.id)
                .order_by(TournamentParticipant.seed)
            )
            participants = participants_result.scalars().all()

            if len(participants) < 2:
                logger.warning(f"Group {group.name} has less than 2 participants, skipping")
                continue

            # Создаем команды для группы (каждый участник = команда)
            # В рамках Round Robin каждая пара играет один матч
            for p1, p2 in combinations(participants, 2):
                # Проверяем, существуют ли уже команды для этих участников
                team1 = await StageService._get_or_create_team_for_participant(
                    db, stage.tournament_id, p1, group.name
                )
                team2 = await StageService._get_or_create_team_for_participant(
                    db, stage.tournament_id, p2, group.name
                )

                encounter = Encounter(
                    tournament_id=stage.tournament_id,
                    stage_id=stage.id,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    stage_name=f"{stage.name} - {group.name}",
                    round_number=1,
                    is_auto_created=1,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(encounter)
                encounters.append(encounter)

        await db.commit()

        # Возвращаем все созданные encounter'ы
        for enc in encounters:
            await db.refresh(enc)

        logger.info(f"Created {len(encounters)} round robin encounters for stage {stage.id}")
        return encounters

    @staticmethod
    async def _generate_swiss(db: AsyncSession, stage: TournamentStage) -> List[Encounter]:
        """
        Швейцарская система: пары формируются на основе текущих результатов.
        Для первого раунда — случайный или по посеву.
        Для последующих — участники с одинаковым количеством очков играют друг с другом.
        """
        # Получаем участников этапа (без групп, все в одном списке)
        participants_result = await db.execute(
            select(TournamentParticipant)
            .where(TournamentParticipant.tournament_id == stage.tournament_id)
            .where(TournamentParticipant.group_id.is_(None))
            .order_by(TournamentParticipant.seed)
        )
        participants = participants_result.scalars().all()

        if len(participants) < 2:
            raise HTTPException(status_code=400, detail="Not enough participants for swiss")

        # Для швейцарки пока создаем только первый раунд по посеву
        # В будущем логика будет расширена для dynamic pairing
        encounters = []

        # Создаем команды
        teams = []
        for p in participants:
            team = await StageService._get_or_create_team_for_participant(
                db, stage.tournament_id, p, "Swiss"
            )
            teams.append((p, team))

        # Формируем пары первого раунда: 1 vs 2, 3 vs 4, etc.
        for i in range(0, len(teams) - 1, 2):
            _, team1 = teams[i]
            _, team2 = teams[i + 1]

            encounter = Encounter(
                tournament_id=stage.tournament_id,
                stage_id=stage.id,
                team1_id=team1.id,
                team2_id=team2.id,
                stage_name=stage.name,
                round_number=1,
                is_auto_created=1,
                created_at=datetime.now(timezone.utc)
            )
            db.add(encounter)
            encounters.append(encounter)

        # Если нечетное количество, последний получает bye (пропускает раунд)
        if len(teams) % 2 == 1:
            logger.info(f"Participant {teams[-1][0].user_id} gets a bye in round 1")

        await db.commit()

        for enc in encounters:
            await db.refresh(enc)

        logger.info(f"Created {len(encounters)} swiss encounters for stage {stage.id}")
        return encounters

    @staticmethod
    async def _generate_single_elimination(db: AsyncSession, stage: TournamentStage) -> List[Encounter]:
        """
        Одиночная сетка: участники играют до первого поражения.
        Количество матчей = N - 1 (где N — количество участников).
        """
        participants_result = await db.execute(
            select(TournamentParticipant)
            .where(TournamentParticipant.tournament_id == stage.tournament_id)
            .order_by(TournamentParticipant.seed)
        )
        participants = participants_result.scalars().all()

        if len(participants) < 2:
            raise HTTPException(status_code=400, detail="Not enough participants for single elimination")

        # Дополняем до степени 2 (2, 4, 8, 16...) с помощью bye
        n = len(participants)
        next_power_of_2 = 1
        while next_power_of_2 < n:
            next_power_of_2 *= 2

        byes_count = next_power_of_2 - n

        # Создаем команды
        teams = []
        for p in participants:
            team = await StageService._get_or_create_team_for_participant(
                db, stage.tournament_id, p, "Elimination"
            )
            teams.append(team)

        # Формируем первый раунд
        # Посев: 1 vs N, 2 vs (N-1), etc. (standard seeding)
        encounters = []
        round_number = 1
        current_round_teams = list(teams)

        # Если есть bye, первые `byes_count` участников автоматически проходят
        if byes_count > 0:
            logger.info(f"First {byes_count} participants get a bye to round 2")

        # Создаем матчи первого раунда (без bye участников)
        first_round_start = byes_count
        for i in range(first_round_start, len(current_round_teams), 2):
            if i + 1 < len(current_round_teams):
                team1 = current_round_teams[i]
                team2 = current_round_teams[len(current_round_teams) - 1 - (i - first_round_start)]

                encounter = Encounter(
                    tournament_id=stage.tournament_id,
                    stage_id=stage.id,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    stage_name=stage.name,
                    round_number=round_number,
                    is_auto_created=1,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(encounter)
                encounters.append(encounter)

        await db.commit()

        for enc in encounters:
            await db.refresh(enc)

        logger.info(f"Created {len(encounters)} single elimination encounters for stage {stage.id}")
        return encounters

    @staticmethod
    async def _generate_double_elimination(db: AsyncSession, stage: TournamentStage,
                                           upper_participants: Optional[List[TournamentParticipant]] = None,
                                           lower_participants: Optional[List[TournamentParticipant]] = None) -> List[Encounter]:
        """
        Двойная сетка: верхняя и нижняя сетки.
        Поражение в верхней сетке -> падение в нижнюю.
        Поражение в нижней сетке -> выбывание.
        """
        # Если участники уже переданы (после группового этапа), используем их
        # Иначе берем всех участников турнира
        if upper_participants is None:
            upper_participants_result = await db.execute(
                select(TournamentParticipant)
                .where(TournamentParticipant.tournament_id == stage.tournament_id)
                .order_by(TournamentParticipant.seed)
            )
            upper_participants = upper_participants_result.scalars().all()

        if lower_participants is None:
            lower_participants = []

        if len(upper_participants) < 2:
            raise HTTPException(status_code=400, detail="Not enough participants for double elimination")

        encounters = []

        # Создаем команды для верхней сетки
        upper_teams = []
        for p in upper_participants:
            team = await StageService._get_or_create_team_for_participant(
                db, stage.tournament_id, p, "Upper"
            )
            upper_teams.append(team)

        # Создаем команды для нижней сетки (если есть)
        lower_teams = []
        for p in lower_participants:
            team = await StageService._get_or_create_team_for_participant(
                db, stage.tournament_id, p, "Lower"
            )
            lower_teams.append(team)

        # Формируем первый раунд верхней сетки
        for i in range(0, len(upper_teams) - 1, 2):
            team1 = upper_teams[i]
            team2 = upper_teams[i + 1]

            encounter = Encounter(
                tournament_id=stage.tournament_id,
                stage_id=stage.id,
                team1_id=team1.id,
                team2_id=team2.id,
                stage_name=f"{stage.name} - Upper",
                round_number=1,
                is_auto_created=1,
                created_at=datetime.now(timezone.utc)
            )
            db.add(encounter)
            encounters.append(encounter)

        # Формируем первый раунд нижней сетки (если есть участники)
        if len(lower_teams) >= 2:
            for i in range(0, len(lower_teams) - 1, 2):
                team1 = lower_teams[i]
                team2 = lower_teams[i + 1]

                encounter = Encounter(
                    tournament_id=stage.tournament_id,
                    stage_id=stage.id,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    stage_name=f"{stage.name} - Lower",
                    round_number=1,
                    is_auto_created=1,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(encounter)
                encounters.append(encounter)

        await db.commit()

        for enc in encounters:
            await db.refresh(enc)

        logger.info(f"Created {len(encounters)} double elimination encounters for stage {stage.id}")
        return encounters

    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ============================================================

    @staticmethod
    async def _get_or_create_team_for_participant(
        db: AsyncSession, tournament_id: int, participant: TournamentParticipant, group_name: str
    ) -> Team:
        """
        Получает или создает команду для участника.
        В контексте группового этапа каждый участник = отдельная команда.
        """
        # Проверяем, есть ли уже команда для этого участника в этом турнире
        team_result = await db.execute(
            select(Team).where(
                and_(
                    Team.tournament_id == tournament_id,
                    Team.captain_user_id == participant.user_id
                )
            )
        )
        team = team_result.scalar_one_or_none()

        if team:
            return team

        # Создаем новую команду
        team = Team(
            tournament_id=tournament_id,
            name=f"{group_name} - User {participant.user_id}",
            captain_user_id=participant.user_id
        )
        db.add(team)
        await db.flush()  # Не коммитим здесь, чтобы не прерывать транзакцию
        return team

    # ============================================================
    # ПРОДВИЖЕНИЕ МЕЖДУ ЭТАПАМИ
    # ============================================================

    @staticmethod
    async def advance_to_next_stage(db: AsyncSession, current_stage_id: int) -> dict:
        """
        Ключевая функция продвижения участников с завершенного этапа на следующий.

        Логика:
        1. Определяет итоговые места участников в завершенном этапе.
        2. Извлекает advancement_config из settings этапа.
        3. Формирует списки участников для следующего этапа на основе seeding_rule.
        4. Вызывает генератор матчей для следующего этапа.

        Возвращает: {
            "next_stage_id": int,
            "advanced_participants": int,
            "upper_bracket_count": int,
            "lower_bracket_count": int,
            "encounters_created": int
        }
        """
        # Получаем текущий этап
        current_stage_result = await db.execute(
            select(TournamentStage)
            .options(joinedload(TournamentStage.groups))
            .where(TournamentStage.id == current_stage_id)
        )
        current_stage = current_stage_result.scalar_one_or_none()

        if not current_stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        # Получаем следующий этап
        next_stage_result = await db.execute(
            select(TournamentStage).where(
                and_(
                    TournamentStage.tournament_id == current_stage.tournament_id,
                    TournamentStage.stage_number == current_stage.stage_number + 1
                )
            )
        )
        next_stage = next_stage_result.scalar_one_or_none()

        if not next_stage:
            raise HTTPException(status_code=400, detail="No next stage configured")

        # Извлекаем настройки продвижения
        settings = current_stage.settings or {}
        advancement_config = settings.get("advancement_config")

        if not advancement_config:
            raise HTTPException(status_code=400, detail="No advancement configuration found")

        # Определяем итоговые места участников
        participants_by_rank = await StageService._calculate_final_rankings(db, current_stage)

        if not participants_by_rank:
            raise HTTPException(status_code=400, detail="No participants found to advance")

        # Применяем правило посева
        seeding_rule = advancement_config.get("seeding_rule")
        rule_params = advancement_config.get("rule_params", {})
        participants_to_advance_per_group = advancement_config.get("participants_to_advance_per_group", 4)

        upper_bracket_list = []
        lower_bracket_list = []

        if seeding_rule == SeedingRule.UPPER_LOWER_SPLIT:
            upper_bracket_list, lower_bracket_list = StageService._apply_upper_lower_split(
                participants_by_rank, rule_params, participants_to_advance_per_group
            )
        elif seeding_rule == SeedingRule.CROSS_GROUP_SEEDING:
            upper_bracket_list = StageService._apply_cross_group_seeding(
                participants_by_rank, current_stage, rule_params
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported seeding rule: {seeding_rule}")

        # Обновляем group_id и seed для продвинутых участников
        await StageService._update_participants_for_next_stage(
            db, next_stage, upper_bracket_list, lower_bracket_list
        )

        # Генерируем матчи для следующего этапа
        encounters_created = []
        if next_stage.format == StageFormat.DOUBLE_ELIMINATION:
            encounters_created = await StageService._generate_double_elimination(
                db, next_stage, upper_bracket_list, lower_bracket_list
            )
        elif next_stage.format == StageFormat.SINGLE_ELIMINATION:
            all_advanced = upper_bracket_list + lower_bracket_list
            # Временно обновляем seed для всех
            for idx, p in enumerate(all_advanced):
                p.seed = idx + 1
            encounters_created = await StageService._generate_single_elimination(db, next_stage)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Next stage format {next_stage.format} not supported for advancement yet"
            )

        logger.info(
            f"Advanced {len(upper_bracket_list) + len(lower_bracket_list)} participants "
            f"from stage {current_stage_id} to stage {next_stage.id}"
        )

        return {
            "next_stage_id": next_stage.id,
            "advanced_participants": len(upper_bracket_list) + len(lower_bracket_list),
            "upper_bracket_count": len(upper_bracket_list),
            "lower_bracket_count": len(lower_bracket_list),
            "encounters_created": len(encounters_created)
        }

    @staticmethod
    async def _calculate_final_rankings(db: AsyncSession, stage: TournamentStage) -> List[Dict]:
        """
        Рассчитывает финальные места участников на основе результатов матчей этапа.

        Возвращает список словарей:
        [
            {"participant": TournamentParticipant, "rank": 1, "group": "A", "points": 9, "wins": 3},
            ...
        ]
        """
        # Получаем все группы этапа
        groups_result = await db.execute(
            select(StageGroup)
            .where(StageGroup.stage_id == stage.id)
            .order_by(StageGroup.name)
        )
        groups = groups_result.scalars().all()

        all_ranked = []

        if not groups:
            # Если нет групп, все участники в одном "котле"
            participants_result = await db.execute(
                select(TournamentParticipant)
                .where(TournamentParticipant.tournament_id == stage.tournament_id)
                .order_by(TournamentParticipant.seed)
            )
            participants = participants_result.scalars().all()

            # Считаем очки для каждого
            participant_stats = await StageService._calculate_participant_stats(db, stage, participants)

            for idx, (p, stats) in enumerate(participant_stats.items()):
                all_ranked.append({
                    "participant": p,
                    "rank": idx + 1,
                    "group": None,
                    "points": stats.get("points", 0),
                    "wins": stats.get("wins", 0),
                    "losses": stats.get("losses", 0),
                })

            return all_ranked

        # Для каждой группы считаем статистику
        for group in groups:
            participants_result = await db.execute(
                select(TournamentParticipant)
                .where(TournamentParticipant.group_id == group.id)
                .order_by(TournamentParticipant.seed)
            )
            participants = participants_result.scalars().all()

            participant_stats = await StageService._calculate_participant_stats(db, stage, participants)

            # Сортируем внутри группы по очкам (убывание)
            sorted_participants = sorted(
                participant_stats.items(),
                key=lambda x: (x[1].get("points", 0), x[1].get("wins", 0), -x[1].get("losses", 0)),
                reverse=True
            )

            for rank, (p, stats) in enumerate(sorted_participants, 1):
                all_ranked.append({
                    "participant": p,
                    "rank": rank,
                    "group": group.name,
                    "points": stats.get("points", 0),
                    "wins": stats.get("wins", 0),
                    "losses": stats.get("losses", 0),
                })

        return all_ranked

    @staticmethod
    async def _calculate_participant_stats(
        db: AsyncSession, stage: TournamentStage, participants: List[TournamentParticipant]
    ) -> Dict[int, Dict]:
        """
        Подсчитывает статистику участника на основе результатов его матчей.

        Возвращает: {user_id: {"wins": 3, "losses": 1, "points": 9}}
        """
        # Собираем team_id для каждого участника
        user_to_team = {}
        for p in participants:
            team_result = await db.execute(
                select(Team).where(
                    and_(
                        Team.tournament_id == stage.tournament_id,
                        Team.captain_user_id == p.user_id
                    )
                )
            )
            team = team_result.scalar_one_or_none()
            if team:
                user_to_team[p.user_id] = team.id

        if not user_to_team:
            return {}

        team_ids = list(user_to_team.values())

        # Получаем все завершенные матчи этапа
        encounters_result = await db.execute(
            select(Encounter).where(
                and_(
                    Encounter.stage_id == stage.id,
                    Encounter.team1_id.in_(team_ids),
                    Encounter.winner_team_id.isnot(None)  # Только завершенные матчи
                )
            )
        )
        encounters = encounters_result.scalars().all()

        # Инициализируем статистику
        stats = {user_id: {"wins": 0, "losses": 0, "points": 0} for user_id in user_to_team.keys()}

        # Настройки очков из settings
        stage_config = stage.settings.get("stage_config", {}) if stage.settings else {}
        points_per_win = stage_config.get("points_per_win", 3)
        points_per_loss = stage_config.get("points_per_loss", 0)

        for enc in encounters:
            # Определяем, какие команды играли и кто победил
            winner_id = enc.winner_team_id
            loser_id = enc.team1_id if enc.team2_id == winner_id else enc.team2_id

            # Находим пользователей по team_id
            for user_id, team_id in user_to_team.items():
                if team_id == winner_id:
                    stats[user_id]["wins"] += 1
                    stats[user_id]["points"] += points_per_win
                elif team_id == loser_id:
                    stats[user_id]["losses"] += 1
                    stats[user_id]["points"] += points_per_loss

        return stats

    @staticmethod
    def _apply_upper_lower_split(
        participants_by_rank: List[Dict],
        rule_params: Dict,
        participants_to_advance_per_group: int
    ) -> Tuple[List[TournamentParticipant], List[TournamentParticipant]]:
        """
        Разделяет участников на верхнюю и нижнюю сетки на основе их мест.

        rule_params пример:
        {
            "upper_bracket_ranks": [1, 2],
            "lower_bracket_ranks": [3, 4]
        }

        Возвращает: (upper_list, lower_list)
        """
        upper_ranks = rule_params.get("upper_bracket_ranks", [])
        lower_ranks = rule_params.get("lower_bracket_ranks", [])

        upper_bracket_list = []
        lower_bracket_list = []

        for p_data in participants_by_rank:
            participant = p_data["participant"]
            rank = p_data["rank"]

            if rank in upper_ranks:
                upper_bracket_list.append(participant)
            elif rank in lower_ranks:
                lower_bracket_list.append(participant)

        # Сортируем по seed внутри каждой группы
        upper_bracket_list.sort(key=lambda p: p.seed or 999)
        lower_bracket_list.sort(key=lambda p: p.seed or 999)

        return upper_bracket_list, lower_bracket_list

    @staticmethod
    def _apply_cross_group_seeding(
        participants_by_rank: List[Dict],
        stage: TournamentStage,
        rule_params: Dict
    ) -> List[TournamentParticipant]:
        """
        Перекрестный посев: A1 vs B2, B1 vs A2, и т.д.

        Возвращает отсортированный список участников для плей-офф.
        """
        # Группируем по группе
        groups_map = {}
        for p_data in participants_by_rank:
            group_name = p_data["group"]
            if group_name not in groups_map:
                groups_map[group_name] = []
            groups_map[group_name].append(p_data)

        # Сортируем каждую группу по рангу
        for group_name in groups_map:
            groups_map[group_name].sort(key=lambda x: x["rank"])

        # Формируем список для перекрестного посева
        # A1, B1, A2, B2, ... (чередование для правильного посева)
        sorted_groups = sorted(groups_map.keys())
        if len(sorted_groups) < 2:
            # Если только одна группа, просто возвращаем всех по порядку
            return [p_data["participant"] for p_data in participants_by_rank]

        group_a = groups_map[sorted_groups[0]]
        group_b = groups_map[sorted_groups[1]]

        result = []
        max_len = max(len(group_a), len(group_b))

        for i in range(max_len):
            if i < len(group_a):
                result.append(group_a[i]["participant"])
            if i < len(group_b):
                result.append(group_b[i]["participant"])

        return result

    @staticmethod
    async def _update_participants_for_next_stage(
        db: AsyncSession,
        next_stage: TournamentStage,
        upper_bracket_list: List[TournamentParticipant],
        lower_bracket_list: List[TournamentParticipant]
    ):
        """
        Обновляет group_id и seed участников для следующего этапа.
        """
        # Получаем группы следующего этапа (если есть)
        groups_result = await db.execute(
            select(StageGroup)
            .where(StageGroup.stage_id == next_stage.id)
            .order_by(StageGroup.name)
        )
        next_groups = groups_result.scalars().all()

        upper_group = None
        lower_group = None

        for g in next_groups:
            if "upper" in g.name.lower():
                upper_group = g
            elif "lower" in g.name.lower():
                lower_group = g

        # Обновляем участников верхней сетки
        for idx, participant in enumerate(upper_bracket_list):
            participant.group_id = upper_group.id if upper_group else None
            participant.seed = idx + 1

        # Обновляем участников нижней сетки
        for idx, participant in enumerate(lower_bracket_list):
            participant.group_id = lower_group.id if lower_group else None
            participant.seed = idx + 1

        await db.flush()
