from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.services import generation_service
from contextlib import asynccontextmanager
from app.database import SessionLocal
import os, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⚒️ NovelForge starting...")
    init_db()
    db = SessionLocal()
    try:
        generation_service.reset_stale_jobs(db)
    finally:
        db.close()
    yield
    logger.info("⚒️ NovelForge shutting down...")

app = FastAPI(title="NovelForge", version="1.0.0", lifespan=lifespan)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Import and include routers
from app.routers import web, projects, chapters, jobs, settings, export

app.include_router(web.router)
app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(jobs.router)
app.include_router(settings.router)
app.include_router(export.router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "NovelForge", "version": "1.0.0"}