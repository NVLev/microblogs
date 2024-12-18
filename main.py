import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import insert, select

from app.add_data import API_KEY, NAMES
from app.api_router import router as api_router
from app.base_models import Base, Follow, Like, Tweet, User
from app.base_router import router as base_router
from app.config import logger
from app.db_helper import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.

    Эта функция обеспечивает закрытие соединения с базой данных,
    когда приложение завершается.

    :param app: объект приложения FastAPI.
    """
    # startup
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with db_helper.session_factory() as session:
        user1 = User(name=NAMES[0], api_key=API_KEY[0])
        user2 = User(name=NAMES[1], api_key=API_KEY[1])
        user3 = User(name=NAMES[2], api_key=API_KEY[2])
        user4 = User(name=NAMES[3], api_key=API_KEY[3])
        user5 = User(name=NAMES[4], api_key=API_KEY[4])
        session.add_all([user1, user2, user3, user4, user5])
        await session.commit()

    async with db_helper.engine.begin() as conn:
        await conn.execute(insert(Follow).values(follower_id=1, following_id=2))
        await session.execute(insert(Follow).values(follower_id=3, following_id=1))
        await session.commit()

    async with db_helper.session_factory() as session:
        tweet1 = Tweet(user_id=1, content="test content1")
        tweet2 = Tweet(user_id=3, content="test content2")
        session.add_all([tweet1, tweet2])
        await session.commit()

    async with db_helper.session_factory() as session:
        like1 = Like(user_id=4, tweet_id=1)
        like2 = Like(user_id=2, tweet_id=2)
        session.add_all([like1, like2])
        await session.commit()

    yield
    # shutdown
    logger.info("Dispose engine")
    await db_helper.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
app.include_router(base_router, prefix="")
# app.mount("/", StaticFiles(directory="static", html=True), name="static")
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    print("Static directory not found, skipping static file mount")


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Accessing path: {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
