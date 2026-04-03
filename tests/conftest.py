import sys
import os
# Ensure pytest discovers `app` regardless of where it is executed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import database  # Import the module to monkeypatch
from app.models.base_class import Base
from app.api.dependencies import get_db

# Use a physical test database file to prevent multi-threaded SQLite :memory: detached connection crashing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Monkey-patch the global app setup so background worker queues natively see the test DB instead of prod DB
database.engine = engine
database.SessionLocal = TestingSessionLocal

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Instruct FastAPI to use our Mock Test Database instead of sql_app.db
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def init_test_db():
    # Setup tables for test environment, tear them down flawlessly afterward
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
