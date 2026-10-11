from fastapi import APIRouter
from app.api import health, cases, evidence, goals, investigations, leads, orchestrator, timeline, analysis

api_router = APIRouter()

# Include Phase 1 Core REST API routers
api_router.include_router(cases.router)
api_router.include_router(evidence.router)
api_router.include_router(goals.router)
api_router.include_router(investigations.router)
api_router.include_router(health.router)
api_router.include_router(leads.router)
api_router.include_router(orchestrator.router)
api_router.include_router(timeline.router)
api_router.include_router(analysis.router)
