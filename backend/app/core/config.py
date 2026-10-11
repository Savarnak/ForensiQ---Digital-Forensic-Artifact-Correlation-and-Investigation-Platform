from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "ARGUS — Agentic Investigation Backbone"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    DEBUG: bool = True
    
    # LLM Settings
    LLM_PROVIDER: str = Field(default="openai", description="LLM provider: openai, anthropic, ollama, google")
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "gpt-4o"
    
    # PostgreSQL Settings
    POSTGRES_USER: str = "argus_user"
    POSTGRES_PASSWORD: str = "argus_password"
    POSTGRES_DB: str = "argus_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    # Neo4j Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "argus_graph_password"
    
    # Qdrant Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    
    # Storage Paths
    EVIDENCE_STORAGE_PATH: str = "./data/evidence"
    SYNTHETIC_DATA_PATH: str = "./data/synthetic"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if os.getenv("USE_POSTGRES", "false").lower() in ("true", "1", "yes"):
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"sqlite+aiosqlite:///./argus_local.db"

settings = Settings()
