import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

# from sqlalchemy.ext.asyncio import AsyncSession
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.base_models import Base, User  # Import Base for dropping tables
from app.db_helper import db_helper
from main import app

NAMES = [
    "Vasya Petrov",
    "Petya Ivanov",
    "Anna Shats",
    "Serafima Re",
    "Danila Sergeev",
    "Joahim Abramyan",
    "Katya Vetrova",
    "Masha Petrova",
]


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    @asynccontextmanager
    async def session_context():
        async for session in db_helper.session_getter():
            try:
                yield session
            finally:
                await session.rollback()

    async with session_context() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
