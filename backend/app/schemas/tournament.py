from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TournamentCreate(BaseModel):
    """Создать турнир (только admin)."""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    format: str = Field(..., pattern="^(mix|draft|start|other)$")
    cover_url: Optional[str] = None
    start_date: datetime
    end_date: datetime
    registration_open: Optional[datetime] = None
    registration_close: Optional[datetime] = None
    checkin_open: Optional[datetime] = None
    checkin_close: Optional[datetime] = None
    max_participants: Optional[int] = 100


class TournamentUpdate(BaseModel):
    """Обновить турнир."""
    title: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    cover_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_open: Optional[datetime] = None
    registration_close: Optional[datetime] = None
    checkin_open: Optional[datetime] = None
    checkin_close: Optional[datetime] = None
    max_participants: Optional[int] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class TournamentResponse(BaseModel):
    """Полный ответ турнира."""
    id: int
    title: str
    description: Optional[str]
    format: str
    cover_url: Optional[str]
    start_date: datetime
    end_date: datetime
    registration_open: Optional[datetime]
    registration_close: Optional[datetime]
    checkin_open: Optional[datetime]
    checkin_close: Optional[datetime]
    status: str
    max_participants: Optional[int]
    participants_count: int
    is_featured: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TournamentShortResponse(BaseModel):
    """Короткий ответ турнира (для списка)."""
    id: int
    title: str
    format: str
    cover_url: Optional[str]
    start_date: datetime
    end_date: datetime
    status: str
    participants_count: int
    max_participants: Optional[int]
    is_featured: bool

    class Config:
        from_attributes = True