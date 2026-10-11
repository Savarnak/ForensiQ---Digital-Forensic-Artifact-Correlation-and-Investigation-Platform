from fastapi import APIRouter
from app.core.config import settings
from app.core.neo4j import neo4j_client
from app.core.qdrant import qdrant_client

router = APIRouter(prefix="/health", tags=["Health & System Status"])

@router.get("")
async def check_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "database": "sqlite_or_postgres_ready",
        "neo4j_connected": neo4j_client.connected,
        "qdrant_connected": qdrant_client.connected
    }
