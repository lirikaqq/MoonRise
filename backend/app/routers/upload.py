"""Эндпоинт для загрузки изображений обложки турнира.

Файлы сохраняются в директорию ``static/covers`` (относительно корня проекта) и
доступны клиенту по пути ``/covers/<filename>``. Этот роут будет подключён в
``backend/app/main.py`` с префиксом ``/api/upload``.
"""

import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_admin

router = APIRouter(tags=["Upload"])


@router.post(
    "/tournaments/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
async def upload_tournament_cover(
    request: Request,
    file: UploadFile = File(...),
    current_admin: Depends = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Загружает обложку турнира.

    Сохраняет файл в ``static/uploads/`` и возвращает URL формата
    ``http://.../static/uploads/<filename>``.
    """

    # Корневая директория проекта: .../backend/app/routers -> .../backend
    uploads_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "static", "uploads")
    )
    os.makedirs(uploads_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    if not ext:
        raise HTTPException(status_code=400, detail="File extension is missing")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(uploads_dir, filename)

    try:
        with open(dest_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    base = str(request.base_url).rstrip("/")
    public_url = f"{base}/static/uploads/{filename}"
    return {"url": public_url}

