from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import init_db
from app.core.neo4j import neo4j_client
from app.core.qdrant import qdrant_client
from app.api.router import api_router

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ARGUS Backend Foundation...")
    await init_db()
    await neo4j_client.connect()
    qdrant_client.connect()
    logger.info("ARGUS Backend Foundation Startup Complete.")
    yield
    logger.info("Shutting down ARGUS Backend Services...")
    await neo4j_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers on /api and /api/v1 for full route compatibility
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "title": settings.PROJECT_NAME,
        "docs": "/api/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
