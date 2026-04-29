import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, init_db
from app.routers import projects, chapters, characters, world, stats, export, settings, generation, jobs

APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("APP_PORT", "8788"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("⭐  NovelForge API starting up...")
    init_db()
    
    # Create data directories
    data_dir = Path(__file__).parent.parent / "data"
    novels_dir = Path(__file__).parent.parent.parent / "novels"
    data_dir.mkdir(parents=True, exist_ok=True)
    novels_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    print("👋  NovelForge API shutting down...")

app = FastAPI(title="NovelForge - AI小说生成管理系统", version="2.0.0", lifespan=lifespan)

# CORS - allow all for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(chapters.router, prefix="/api", tags=["Chapters"])
app.include_router(characters.router, prefix="/api", tags=["Characters"])
app.include_router(world.router, prefix="/api", tags=["World"])
app.include_router(stats.router, prefix="/api", tags=["Stats"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(settings.router, prefix="/api", tags=["ModelConfig"])
app.include_router(generation.router, prefix="/api", tags=["Generation"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])

# Serve frontend in production
static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

@app.get("/")
async def root():
    return {"message": "Novel System API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}