import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Override DATABASE_URL BEFORE any app module loads
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

import pytest
import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_app.db"
test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession, expire_on_commit=False)

# Import app AFTER env is set
from app.main import app
from app.api.dependencies import get_db
from app.models.base_class import Base

# Patch the database module to use test engine
import app.db.database as db_module
db_module.engine = test_engine
db_module.SessionLocal = TestSessionLocal

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Initialize DB once for full session
@pytest.fixture(scope="session", autouse=True)
def init_db():
    async def setup():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(setup())
    yield
    async def teardown():
        await test_engine.dispose()
    asyncio.run(teardown())
    try:
        os.remove("test_app.db")
    except Exception:
        pass

# Async client fixture using httpx + ASGITransport
@pytest.fixture
async def client(init_db):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
