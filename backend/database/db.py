import os
import re
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

Base = declarative_base()

class NeonDatabase:
    _engine = None
    _SessionLocal = None

    @classmethod
    def init(cls):
        if cls._engine is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL is not set")

            async_url = re.sub(r"^postgresql:", "postgresql+asyncpg:", database_url)

            cls._engine = create_async_engine(async_url, echo=True, future=True)
            cls._SessionLocal = sessionmaker(
                bind=cls._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return cls._engine

    @classmethod
    def get_session(cls) -> AsyncSession:
        if cls._SessionLocal is None:
            cls.init()
        return cls._SessionLocal()

    @classmethod
    async def dispose(cls):
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            cls._SessionLocal = None

