"""AIMS FastAPI application entry."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.analysis import router as analysis_router
from backend.api.market import router as market_router
from backend.api.plan2030 import router as plan2030_router
from backend.api.reports import router as reports_router
from backend.storage.database import init_database
from backend.tasks.scheduler import start_scheduler, stop_scheduler

# Configure root logger with size-based rotation when AIMS_LOG_FILE is set
# Default: 10 MB per file, keep 5 backups
log_file = os.environ.get("AIMS_LOG_FILE")
if log_file:
    max_bytes = int(os.environ.get("AIMS_LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    backup_count = int(os.environ.get("AIMS_LOG_BACKUP_COUNT", "5"))
    file_handler = RotatingFileHandler(
        log_file,
        encoding="utf-8",
        mode="a",
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    file_handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"
NO_CACHE_HEADERS = {"Cache-Control": "no-store"}

app = FastAPI(
    title="AIMS",
    description="AI Market Intelligence System",
    version="0.1.0",
)

app.include_router(market_router)
app.include_router(reports_router)
app.include_router(analysis_router)
app.include_router(plan2030_router)


@app.on_event("startup")
def startup():
    init_database()
    start_scheduler()


@app.on_event("shutdown")
def shutdown():
    stop_scheduler()


@app.get("/")
def root():
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX, headers=NO_CACHE_HEADERS)

    return {
        "name": "AIMS",
        "status": "running",
    }


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        class NoCacheStaticFiles(StaticFiles):
            async def get_response(self, path, scope):
                response = await super().get_response(path, scope)
                response.headers["Cache-Control"] = "no-store"
                return response

        app.mount("/assets", NoCacheStaticFiles(directory=assets_dir), name="assets")


    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_fallback(full_path: str):
        requested_file = FRONTEND_DIST / full_path
        if requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(FRONTEND_INDEX, headers=NO_CACHE_HEADERS)
