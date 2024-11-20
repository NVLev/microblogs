import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.config import Settings, DatabaseConfig
from app.db.models import Base
from app.db_helper import DatabaseHelper

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/test_microblogs"


# Create test settings
def get_test_settings() -> Settings:
    test_db_config = DatabaseConfig(
        url=TEST_DATABASE_URL,
        echo=False,
        echo_pool=False,
        pool_size=5,
        max_overflow=5
    )
    settings = Settings()
    settings.db = test_db_config
    return settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_helper() -> AsyncGenerator[DatabaseHelper, None]:
    """Create a test database helper instance."""
    settings = get_test_settings()
    db_helper = DatabaseHelper(
        url=settings.db.url,
        echo=settings.db.echo,
        echo_pool=settings.db.echo_pool,
        pool_size=settings.db.pool_size,
        max_overflow=settings.db.max_overflow,
    )

    # Create all tables
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield db_helper

    # Cleanup
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await db_helper.dispose()


@pytest_asyncio.fixture
async def test_session(test_db_helper) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_db_helper.session_factory() as session:
        yield session
        # Rollback any changes made in the test
        await session.rollback()