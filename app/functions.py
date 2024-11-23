import os
from typing import Optional, Type

from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import delete, func, insert, select, update, Result
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, load_only, selectinload

from app.base_models import Follow, Image, Like, Tweet, User
from app.basic_schema import LikeBase, ResultBase, TweetBase, UserBase, UserData, UserRead
from app.config import logger


async def get_api_key(request):
    logger.info("Начали процесс получение апи ключа")
    api_key = request.headers.get("Authorization")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    return api_key


async def get_user_id_by_api_key(
    session: AsyncSession, api_key: str
) -> int | None:
    logger.info("Стартанули получение id ")
    try:
        stmt = select(User).where(User.api_key == api_key)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            logger.info(f"user id - {user.id}")
            return user.id
        return None
    except ValidationError as e:
        logger.error(f"Ошибка валидации Pydantic: {e}")
        raise HTTPException(status_code=422, detail=f"Ошибка валидации: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error")


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[UserData]:
    try:
        logger.info("Начали выполнение функции по получению объекта Юзера")
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            return None

        logger.info("Начали получение фолловеров юзера")
        followers_stmt = (
            select(User)
            .join(Follow, User.id == Follow.follower_id)
            .where(Follow.following_id == user_id)
        )
        followers_result = await session.execute(followers_stmt)
        followers_data = [
            UserBase(id=f.id, name=f.name) for f in followers_result.scalars()
        ]
        logger.info(f"Получены фолловеры {followers_data}")

        logger.info("Начали получение списка тех, на кого подписан юзер")
        following_stmt = (
            select(User)
            .join(Follow, User.id == Follow.following_id)
            .where(Follow.follower_id == user_id)
        )
        following_result = await session.execute(following_stmt)
        following_data = [
            UserBase(id=f.id, name=f.name) for f in following_result.scalars()
        ]
        logger.info(f"Юзер подписан на {following_data}")

        user_data = UserData(
            id=user.id, name=user.name, followers=followers_data, following=following_data
        )
        return user_data

    except SQLAlchemyError as e:
        logger.exception(f"Ошибка базы данных при получении юзера: {e}")
        return None
    except Exception as e:
        logger.exception(f"Ошибка получения юзера: {e}")
        return None


async def get_tweet_by_id(session: AsyncSession, tweet_id: int) -> Tweet | None:
    stmt = select(Tweet).where(Tweet.id == tweet_id)
    result = await session.execute(stmt)
    tweet = result.scalar_one_or_none()
    if tweet:
        logger.info(f"Твит {tweet} получен")
        return tweet
    return None


async def write_new_tweet(user_id: id, content: str, session: AsyncSession) -> id:
    logger.info("Начали процесс получения ид")
    stmt = insert(Tweet).values(user_id=user_id, content=content).returning(Tweet.id)
    result = await session.execute(stmt)
    tweet_id = result.scalar_one()
    await session.commit()
    logger.info(f"tweet id - {tweet_id}")
    return tweet_id


async def update_tweet_with_media(
    media_ids: list[int],
    tweet_id: int,
    session: AsyncSession,
) -> None:
    try:
        for media_id in media_ids:
            update_tweet_id_query = (
                update(Image).where(Image.id == media_id).values(tweet_id=tweet_id)
            )
            await session.execute(update_tweet_id_query)
            await session.commit()
    except SQLAlchemyError as e:
        error_message = e
        raise HTTPException(status_code=400, detail={error_message})


async def get_media(file_url: str, session: AsyncSession) -> Optional[Image]:
    stmt = select(Image).where(Image.url == file_url)
    result: Result = await session.execute(stmt)
    image: Optional[Image] = result.scalars().one_or_none()
    return image


async def save_media(
    session: AsyncSession, file: UploadFile, user_id: int, file_url: str
)-> Optional[int]:
    try:
        stmt = insert(Image).values(url=file_url).returning(Image.id)
        result = await session.execute(stmt)
        await session.commit()
        image_id: Optional[int] = result.scalar_one()

        if not os.path.exists("media"):
            os.makedirs("media")
        filepath = f"media/{file.filename}"
        with open(filepath, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
        return image_id

    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка базы данных: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранениии файла: {e}")


async def get_tweets_info(session: AsyncSession):
    select_query = (
        select(Tweet).options(
            load_only(Tweet.id, Tweet.content),
            selectinload(Tweet.author),
            selectinload(Tweet.likes),
        )
        # .options(selectinload(Tweet.likes))
    )
    result = await session.execute(select_query)
    tweets = result.scalars().all()
    logger.info(f"Получили твиты {tweets}")
    tweet_responses = []
    for tweet in tweets:
        logger.info(f"Вносим в список {tweet}")
        tweet_responses.append(
            TweetBase(
                id=tweet.id,
                content=tweet.content,
                author=UserBase(id=tweet.author.id, name=tweet.author.name),
                likes=[
                    LikeBase(id=like.id, user_id=like.user_id) for like in tweet.likes
                ],
            )
        )
    return {"result": True, "tweets": tweet_responses}  # Set the 'tweets' field


async def add_like(user_id: int, tweet_id: int, session: AsyncSession):
    try:
        logger.info(
            f"Функция добавления лайка для user id {user_id}, tweet id {tweet_id} запущена"
        )
        new_like = Like(user_id=user_id, tweet_id=tweet_id)
        session.add(new_like)
        await session.commit()
        await session.refresh(new_like)
        logger.info(f"ID лайка: {new_like.id}")
        return new_like.id
    except ValidationError as e:
        logger.error(f"Ошибка валидации Pydantic: {e}")
        raise HTTPException(status_code=422, detail=f"Ошибка валидации: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error")


async def delete_like(user_id: int, tweet_id: int, session: AsyncSession):
    await session.execute(
        delete(Like).filter(Like.tweet_id == tweet_id, Like.user_id == user_id)
    )
    await session.commit()


async def delete_tweet_by_id(tweet_id: int, session: AsyncSession) -> None:
    stmt = delete(Tweet).where(Tweet.id == tweet_id)
    await session.execute(stmt)
    await session.commit()


async def delete_following_by_id(
    follower_id: int, following_id: int, session: AsyncSession
) -> None:
    stmt = delete(Follow).where(
        Follow.follower_id == follower_id, Follow.following_id == following_id
    )
    await session.execute(stmt)
    await session.commit()
    logger.info("Подписка благополучно удалилась")


async def check_follow_user(user_id: int, following_id: int, session: AsyncSession):
    """Проверяет наличие подписки на пользователя."""

    logger.info("Начали выполнение проверки")
    result = await session.execute(
        select(func.count(Follow.id)).where(
            Follow.follower_id == user_id, Follow.following_id == following_id
        )
    )
    count = result.scalar_one()
    logger.info(f"Получили количество подписок: {count}")
    return count > 0


async def create_follow_to_user(
    follower_id: int, following_id: int, session: AsyncSession
) -> bool:
    """Создает новую подписку на пользователя."""
    try:
        logger.info("Начали создание новой подписки")

        stmt = insert(Follow).values(follower_id=follower_id, following_id=following_id)
        await session.execute(stmt)
        await session.commit()
        logger.info("Подписка создана")
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка создания подписки: {e}")
        return False
