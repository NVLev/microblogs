import asyncio
import json
import os

import aiofiles
import pytest
from fastapi import UploadFile
from httpx import AsyncClient
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.add_data import API_KEY, NAMES
from app.base_models import Tweet
from app.config import logger
from app.functions import add_like, get_media


@pytest.mark.asyncio
async def test_get_user(async_client, db_session):
    url = "/api/users/2"
    headers = {"api-key": API_KEY[0]}
    resp = await async_client.get(url, headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.text) == {
        "result": True,
        "user": {
            "id": 2,
            "name": NAMES[1],
            "following": [],
            "followers": [{"id": 1, "name": NAMES[0]}],
        },
    }


@pytest.mark.asyncio
async def test_get_tweets(async_client, db_session):
    url = "/api/tweets"
    headers = {"api-key": API_KEY[1]}
    resp = await async_client.get(url, headers=headers)
    assert resp.status_code == 200
    assert len(json.loads(resp.text)) >= 1


@pytest.mark.asyncio
async def test_create_tweet(async_client, db_session):
    url = "/api/tweets"
    headers = {"api-key": API_KEY[0]}
    data = {"tweet_data": "Test tweet", "image_ids": [1, 2]}
    resp = await async_client.post(url, headers=headers, json=data)
    assert resp.status_code == 200
    assert json.loads(resp.text)["result"] is True


@pytest.mark.asyncio
async def test_post_media_with_tweet(async_client, db_session):
    """
    Проверяет функцию добавления изображения к твиту
    """
    current_dir = os.getcwd()
    file_dir = os.path.join(current_dir, "tests/test.jpg")
    url = "/api/medias"
    headers = {"api-key": API_KEY[0]}

    async with aiofiles.open(file_dir, "rb") as f:
        image_data = await f.read()
        files = {"file": ("test.jpg", image_data, "image/jpeg")}
        resp = await async_client.post(url, headers=headers, files=files)

        assert resp.status_code == 201
        assert json.loads(resp.text) == {"result": True, "media_id": 1}


@pytest.mark.asyncio
async def test_post_like_to_tweet(async_client, db_session):
    """
    Проверяет функцию добавления лайка к твиту
    """
    user_id = 1
    tweet_id = 1
    api_key = API_KEY[0]
    headers = {"api-key": api_key}
    logger.info("Проверяем, что лайк не существует")
    query = select(Tweet).where(
        and_(Tweet.id == tweet_id, Tweet.likes.any(user_id=user_id))
    )
    result = await db_session.execute(query)
    like = result.scalar_one_or_none()
    assert like is None

    logger.info("Отправляем запрос на добавление лайка")
    await add_like(user_id=user_id, tweet_id=tweet_id, session=db_session)

    logger.info("Проверяем, что лайк был добавлен")
    query = select(Tweet).where(
        and_(Tweet.id == tweet_id, Tweet.likes.any(user_id=user_id))
    )
    result = await db_session.execute(query)
    like = result.scalar_one_or_none()
    assert like is not None


@pytest.mark.asyncio
async def test_delete_tweet(async_client, db_session):
    """
    Проверяет функцию удаления твита

    """
    url = f"/api/tweets/1"
    headers = {"api-key": API_KEY[0]}
    resp = await async_client.delete(url, headers=headers)
    assert resp.status_code == 202
    assert json.loads(resp.text) == {"result": True}


@pytest.mark.asyncio
async def test_post_follow_to_user(async_client, db_session):
    """
    Проверяет функцию подписки на пользователя

    """
    url = f"/api/users/2/follow"
    headers = {"api-key": API_KEY[1]}
    resp = await async_client.post(url, headers=headers)
    assert resp.status_code == 202
    assert json.loads(resp.text)["result"] is True


@pytest.mark.asyncio
async def test_post_follow_to_user_already_following(async_client, db_session):
    """
    Проверяет функцию подписки на пользователя, если он уже подписан
    :param async_client:
    :param db_session:
    :return:
    """
    url = f"/api/users/2/follow"
    headers = {"api-key": API_KEY[0]}
    # await async_client.post(url, headers=headers)
    resp = await async_client.post(url, headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Запрос не обработан. Пользователь уже подписан"


@pytest.mark.asyncio
async def test_delete_follow_from_user(async_client, db_session):
    """
    Проверяет функцию удаления подписки на пользователя

    """
    url = f"/api/users/2/follow"
    headers = {"api-key": API_KEY[0]}
    resp = await async_client.delete(url, headers=headers)
    assert resp.status_code == 202
    assert json.loads(resp.text) == {"result": True}
