from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.base_models import User

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


async def test_add_users(async_client: AsyncSession) -> None:
    # Добавляем первого пользователя
    stmt_user = insert(User).values(name=NAMES[0], api_key=API_KEY[0])
    await async_client.execute(stmt_user)
    await async_client.commit()


    # Добавляем второго пользователя
    stmt_user = insert(User).values(name=NAMES[1], api_key=API_KEY[1]).returning(User)
    user = await async_client.scalar(stmt_user)


    await async_client.commit()
    assert user.id == 2
