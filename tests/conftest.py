"""
Test configuration for pytest
"""

import pytest
import asyncio
from httpx import AsyncClient
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
from core.database import init_db, get_db, Base
from core.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create test database"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_db):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client, test_db):
    """Create authenticated test client"""
    from core.auth import get_password_hash
    from core.database import User
    
    # Create test user
    db = test_db()
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        is_admin=True,
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.close()
    
    # Login and get token
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    response = await client.post("/api/auth/token", data=login_data)
    token = response.json()["access_token"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    yield client
