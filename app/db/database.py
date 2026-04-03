import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv

load_dotenv()

raw_url = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# Patch sync URL schemes to their async driver equivalents
if "postgresql+asyncpg" in raw_url or "sqlite+aiosqlite" in raw_url:
    # Already async-compatible (e.g. set by test conftest)
    SQLALCHEMY_DATABASE_URL = raw_url
elif raw_url.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif raw_url.startswith("sqlite://"):
    SQLALCHEMY_DATABASE_URL = raw_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
else:
    SQLALCHEMY_DATABASE_URL = raw_url

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)
