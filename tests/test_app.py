import json

import pytest
import asyncio
from httpx import AsyncClient
from fastapi import UploadFile
from app.add_data import API_KEY, NAMES
from app.basic_schema import UserRead
from app.basic_schema import TweetRead, TweetCreate, TweetResponse
from app.base_models import User
from app.base_models import Tweet
from app.config import logger
from app.db_helper import db_helper
from sqlalchemy.ext.asyncio import AsyncSession

from app.functions import get_media, add_like


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
    assert json.loads(resp.text)['result'] is True


@pytest.mark.asyncio
async def test_post_media_with_tweet(async_client, db_session):
    """
    Проверяет функцию добавления изображения к твиту
    """
    user_id = 1
    api_key = API_KEY[0]
    file_url = f"{api_key}_test.jpg"
    file = UploadFile("test.jpg")
    headers = {"api-key": api_key}
    logger.info('Проверяем, что медиафайл не существует')
    media = await get_media(file_url=file_url, session=db_session)
    assert media is None
    logger.info('Отправляем запрос на добавление медиафайла')
    response = await async_client.post(
        "/medias", headers=headers, files={"file": file}
    )
    assert response.status_code == 201
    assert response.json() == {"result": True, "media_id": 1}
    logger.info('Проверяем, что медиафайл был добавлен')
    media = await get_media(file_url=file_url, session=db_session)
    assert media is not None
    assert media.url == file_url
    assert media.id == user_id


@pytest.mark.asyncio
async def test_post_like_to_tweet(async_client, db_session):
    """
    Проверяет функцию добавления лайка к твиту
    """
    user_id = 1
    tweet_id = 1
    api_key = API_KEY[0]
    headers = {"api-key": api_key}
    logger.info('Проверяем, что лайк не существует')
    like = await db_session.execute(
        db_session.query(Tweet).filter(Tweet.id == tweet_id).filter(Tweet.likes.any(user_id=user_id))
    ).fetchone()
    assert like is None
    logger.info('Отправляем запрос на добавление лайка')
    response = await async_client.post(f"/tweets/{tweet_id}/likes", headers=headers)
    assert response.status_code == 201
    assert response.json() == {"result": True}
    logger.info('Проверяем, что лайк был добавлен')
    like = await db_session.execute(
        db_session.query(Tweet).filter(Tweet.id == tweet_id).filter(Tweet.likes.any(user_id=user_id))
    ).fetchone()
    assert like is not None


@pytest.mark.asyncio
async def test_delete_likes_from_tweet(async_client, db_session):
    """
    Проверяет функцию удаления лайка из твита
    """
    user_id = 1
    tweet_id = 1
    api_key = API_KEY[0]
    headers = {"api-key": api_key}
    logger.info('Добавляем лайк к твиту')
    await add_like(user_id=user_id, tweet_id=tweet_id, session=db_session)
    logger.info('Проверяем, что лайк существует')
    like = await db_session.execute(
        db_session.query(Tweet).filter(Tweet.id == tweet_id).filter(Tweet.likes.any(user_id=user_id))
    ).fetchone()
    assert like is not None
    logger.info('Отправляем запрос на удаление лайка')
    response = await async_client.delete(f"/tweets/{tweet_id}/likes", headers=headers)
    assert response.status_code == 202
    assert response.json() == {"result": True}
    logger.info('Проверяем, что лайк был удален')
    like = await db_session.execute(
        db_session.query(Tweet).filter(Tweet.id == tweet_id).filter(Tweet.likes.any(user_id=user_id))
    ).fetchone()
    assert like is None

