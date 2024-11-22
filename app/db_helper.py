import os
import sys
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import logger, settings

# from module_26_fastapi.homework.config.config import settings


class DatabaseHelper:
    """
    Класс подключения к базе данных, который обеспечивает подключение и управление сессией.
    """

    def __init__(
        self,
        url: str,
        echo: bool = True,
        echo_pool: bool = True,
        pool_size: int = 10,
        max_overflow: int = 10,
    ) -> None:
        """
        Alustaa tietokanta-avustajan.
        """
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        """
        Закрывает соединение
        """
        await self.engine.dispose()
        print("dispose engine")

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Возвращает новый сеанс работы с базой данных

        :return: Асинхронная сессия
        """
        session = self.session_factory()
        async with session:
            yield session


db_helper = DatabaseHelper(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)
