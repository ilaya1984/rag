from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import get_settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{get_settings().POSTGRES_USER}:{get_settings().POSTGRES_PASSWORD}@{get_settings().POSTGRES_HOST}/{get_settings().POSTGRES_DB}"
engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=80,
        max_overflow=0
    )

SessionLocal = sessionmaker(class_=AsyncSession, autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency to get a session for async use
async def get_db():
    async with SessionLocal() as db:
        yield db


# Function to create all tables asynchronously
async def create_tables():
    # First enable PostGIS extension
    async with engine.begin() as conn:
        pass
        # await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        # Then create tables
        # await conn.run_sync(Base.metadata.create_all)


async def get_db_session():
    """Get an async database session for use in non-endpoint functions"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        await db.close()
        raise e
