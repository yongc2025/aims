"""AIMS FastAPI application entry."""

from fastapi import FastAPI

from backend.api.market import router as market_router
from backend.api.reports import router as reports_router

app = FastAPI(
    title="AIMS",
    description="AI Market Intelligence System",
    version="0.1.0",
)

app.include_router(market_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {
        "name": "AIMS",
        "status": "running",
    }
