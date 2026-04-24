from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Literal
from app.constants import VALID_ROLES, VALID_RANKS, VALID_APPLICATION_STATUSES


class ParticipantCore(BaseModel):
    """Унифицированная схема данных участника турнира."""
    id: int                     # ID записи TournamentParticipant
    user_id: int
    display_name: str           # Игровой никнейм (для заголовков)
    discord_tag: str            # Discord username (для D: тега)
    battle_tag: str             # Battle.net тег (для B: тега)
    primary_role: Literal['tank', 'dps', 'sup', 'flex']
    secondary_role: Literal['tank', 'dps', 'sup', 'flex']
    bio: str
    notes: str
    rank: Optional[str] = None
    avatar_url: Optional[str] = None
    is_captain: bool
    is_allowed: bool
    status: str                 # pending / registered / checkedin / rejected
    submitted_at: datetime      # registered_at

    # Для обратной совместимости можно включить исходные application_data
    application_data: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class ParticipantResponse(BaseModel):
    """Ответ API с участниками (список ParticipantCore)."""
    participants: list[ParticipantCore]


# Вспомогательная функция для извлечения полей из application_data и User
def normalize_participant_data(
    participant_obj,
    user_obj,
    battletag: Optional[str] = None
) -> dict:
    """
    Создает словарь с данными участника в соответствии с ParticipantCore.
    """
    # 1. Парсим application_data
    app_data = {}
    if participant_obj.application_data:
        if isinstance(participant_obj.application_data, str):
            try:
                import json
                app_data = json.loads(participant_obj.application_data)
            except:
                app_data = {}
        elif isinstance(participant_obj.application_data, dict):
            app_data = participant_obj.application_data
        else:
            app_data = {}
    
    # 2. Вспомогательная функция для нормализации ролей
    def normalize_role(role: Optional[str]) -> str:
        if not role:
            return None
        role_lower = role.strip().lower()
        # Маппинг псевдонимов: конвертируем support → sup, остальные оставляем как есть
        role_map = {
            'sup': 'sup',
            'support': 'sup',
            'tank': 'tank',
            'dps': 'dps',
            'flex': 'flex',
        }
        # Если роль есть в маппинге, возвращаем каноническое значение
        if role_lower in role_map:
            return role_map[role_lower]
        # Если роль уже в VALID_ROLES, возвращаем как есть (но VALID_ROLES содержит 'support', нужно конвертировать)
        if role_lower in VALID_ROLES:
            if role_lower == 'support':
                return 'sup'
            return role_lower
        # Иначе возвращаем None (будет использован fallback)
        return None
    
    # 3. Определяем поля по приоритету
    
    # primary_role
    primary_role = (
        normalize_role(app_data.get('primary_role')) or
        normalize_role(user_obj.primary_role) or
        'flex'
    )
    
    # secondary_role
    secondary_role = (
        normalize_role(app_data.get('secondary_role')) or
        normalize_role(user_obj.secondary_role) or
        'flex'
    )
    
    # bio
    bio = (
        app_data.get('bio') or
        app_data.get('notes') or
        user_obj.bio or
        ''
    )
    
    # notes
    notes = (
        app_data.get('notes') or
        ''
    )
    
    # battle_tag
    battle_tag = (
        app_data.get('battle_tag') or
        app_data.get('battletag_value') or
        battletag or
        '?'
    )
    
    # discord_tag
    discord_tag = (
        app_data.get('discord_tag') or
        user_obj.username or
        '?'
    )
    
    # display_name
    display_name = (
        app_data.get('display_name') or
        user_obj.display_name or
        user_obj.username or
        '?'
    )
    
    # rank
    rank = app_data.get('rank')
    
    # avatar_url
    avatar_url = user_obj.avatar_url

    return {
        'id': participant_obj.id,
        'user_id': participant_obj.user_id,
        'display_name': display_name,
        'discord_tag': discord_tag,
        'battle_tag': battle_tag,
        'primary_role': primary_role,
        'secondary_role': secondary_role,
        'bio': bio,
        'notes': notes,
        'rank': rank,
        'avatar_url': avatar_url,
        'is_captain': participant_obj.is_captain,
        'is_allowed': participant_obj.is_allowed,
        'status': participant_obj.status,
        'submitted_at': participant_obj.registered_at,
        'application_data': app_data,
    }