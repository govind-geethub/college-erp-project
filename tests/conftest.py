"""
Pytest configuration and test database fixture.
Uses an isolated in-memory SQLite database so tests are completely hermetic
and do not mutate the local development database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.seed_data import seed_database

# In-memory test engine with StaticPool to keep single thread memory alive across queries
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """Create fresh database schema and seed data for every test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    seed_database(session)
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
