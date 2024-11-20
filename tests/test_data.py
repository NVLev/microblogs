from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.base_models import User
import pytest

NAMES = [
    "John Doe",
    "Maria Vasilieva",
    "Sergey",
    "Loui Vitton",
    "Prada",
    "Slava Zaitsev",
    "Luda Prihodko",
]
API_KEY = ["test_api", "api_test"]

@pytest.mark.asyncio
async def test_add_users(async_client, db_session) -> None:
    # Добавляем первого пользователя
    stmt_user = insert(User).values(name=NAMES[0], api_key=API_KEY[0])
    await db_session.execute(stmt_user)
    await db_session.commit()


    # Добавляем второго пользователя
    stmt_user = insert(User).values(name=NAMES[1], api_key=API_KEY[1]).returning(User)
    user = await db_session.scalar(stmt_user)
    await db_session.commit()

    assert user.id == 7
