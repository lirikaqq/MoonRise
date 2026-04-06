# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import (
    auth,
    homepage,
    matches,
    players,
    tournaments,
    users,
    draft, # Оставляем только один импорт модуля
)
from app.ws import draft_ws

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database and tables checked/created.")
    yield

app = FastAPI(
    title="MoonRise API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Убедись, что твой фронт на этом порту
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Подключаем роутеры ---
# Для всех роутеров, кроме draft, мы можем задавать префикс здесь.
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(homepage.router, prefix="/api/homepage", tags=["Homepage"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(tournaments.router, prefix="/api/tournaments", tags=["Tournaments"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(draft_ws.router)
app.include_router(draft.public_router)

# ДЛЯ DRAFT РОУТЕРА ПРЕФИКС НЕ УКАЗЫВАЕМ, т.к. он уже есть в draft.py
app.include_router(draft.router)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to MoonRise API!"}