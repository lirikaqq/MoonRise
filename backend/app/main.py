from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.database import init_db, engine

from app.routers import (
    auth,
    homepage,
    matches,
    players,
    tournaments,
    users,
    draft,
    draft_public,
    stages,
    admin_teams
)
from app.config import settings
from app.ws import draft_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database and tables checked/created.")
    
    os.makedirs("static/uploads", exist_ok=True)
    print("Static uploads directory checked/created.")
    
    yield
    await engine.dispose()
    print("Database connections closed.")


app = FastAPI(
    title="MoonRise API",
    lifespan=lifespan,
    redirect_slashes=False   # ← Отключаем автоматический редирект со слешем
)

# === Монтирование статики ===
app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

# === CORS (расширенный для Docker) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://host.docker.internal:5173",
        "http://localhost",
    ],
    allow_origin_regex=r"http://.*\.local:5173",  # на всякий случай
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(homepage.router, prefix="/api/homepage", tags=["Homepage"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(tournaments.router, prefix="/api/tournaments", tags=["Tournaments"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(draft_ws.router)
app.include_router(draft.router)
app.include_router(draft_public.router)
app.include_router(stages.router)

# Dev-only роутеры
if settings.ENVIRONMENT != "production":
    from app.routers import dev
    app.include_router(dev.router)
    print("⚠️  Dev endpoints ENABLED (ENVIRONMENT != production)")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to MoonRise API!"}