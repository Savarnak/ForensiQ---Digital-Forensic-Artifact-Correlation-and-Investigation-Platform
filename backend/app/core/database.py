from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import logger

db_url = settings.get_database_url()
logger.info(f"Initializing database engine: {db_url}")

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    # Import all models to ensure mappers registered
    import app.models # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Check and migrate leads table columns for SQLite/PostgreSQL
        try:
            res = await conn.execute(text("PRAGMA table_info(leads)"))
            cols = [row[1] for row in res.fetchall()]
            if cols:
                if "priority" not in cols:
                    await conn.execute(text("ALTER TABLE leads ADD COLUMN priority VARCHAR(20) DEFAULT 'MEDIUM'"))
                if "supporting_findings" not in cols:
                    await conn.execute(text("ALTER TABLE leads ADD COLUMN supporting_findings JSON DEFAULT '[]'"))
                if "reasoning_factors" not in cols:
                    await conn.execute(text("ALTER TABLE leads ADD COLUMN reasoning_factors JSON DEFAULT '[]'"))
                if "disclaimer" not in cols:
                    await conn.execute(text("ALTER TABLE leads ADD COLUMN disclaimer TEXT DEFAULT 'Investigative aid provided for officer/analyst review. Does not constitute a determination of guilt or administrative finding.'"))
        except Exception as e:
            logger.debug(f"Schema column check skipped or failed: {e}")

    logger.info("Database tables verified/created successfully.")
