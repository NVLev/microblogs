from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi import (
                    APIRouter,
                    Depends,
                    HTTPException,
                    status,
                    Request,
                    UploadFile,
                    File
                )
from sqlalchemy.ext.asyncio import (
                                    AsyncSession,
                                    )

from app.base_models import Tweet
from app.basic_schema import (
    UserRead,
    TweetCreate, TweetResponse, TweetRead, ResultBase, MediaRead
)
from app.functions import (
    get_user_id_by_api_key,
    get_user_by_id,
    write_new_tweet,
    get_tweets_info,
    get_tweet_by_id,
    delete_tweet_by_id,
    add_like,
    delete_like,
    check_follow_user,
    create_follow_to_user,
    delete_following_by_id, update_tweet_with_media, save_media, get_media
)
from app.db_helper import db_helper
from app.config import logger
from error_handling import handle_api_errors

router = APIRouter(prefix='/api', tags=['Работа с микроблогами'])




test_user = {
    "result": "true",
    "user": {
        "id": 1,
        "name": "Vasya",
        "followers": [
            {
                "id": 2,
                "name": "Petya"
            }
        ],
        "following": [
            {
                "id": 3,
                "name": "Serafima"
            }
        ]
    }
}

@router.get(
    "/users/me",
    response_model=UserRead,
    summary="Получение информации о своем профиле по api ключу",
    description="Эндпоинт для получения информации о своем профиле",

)
@handle_api_errors()
async def get_users_me(request: Request, session: AsyncSession = Depends(db_helper.session_getter),
    ):

    api_key: str = request.headers.get("api-key")
    user_id = await get_user_id_by_api_key(session=session, api_key=api_key)
    if user_id:
        user = await get_user_by_id(session=session, user_id=user_id)
        if user:
            logger.info('Получен юзер')
            return {"result": True, "user": user}
        else:
            logger.error(f"Пользователь с id={id} не найден")
            raise HTTPException(
                status_code=401, detail="Ошибка ввода данных"
            )
    else:
        logger.error(f"id={id} не найден")
        raise HTTPException(
            status_code=401, detail="Ошибка ввода данных"
        )


@router.get(
    "/users/{id}",
    summary="Получение информации о пользователе по ID",
    description="Эндпоинт для получения информации о пользователе в соответствии с его ID",
response_model=UserRead,
    status_code=200
    )
async def get_user(id: int,
        session: AsyncSession = Depends(db_helper.session_getter),
    ):
    try:
        user = await get_user_by_id(session=session, user_id=id)
        if user:
            logger.info('Получен юзер')
            return {"result": True, "user": user}
        else:
            logger.error(f"Пользователь с id={id} не найден")
            raise HTTPException(
                status_code=401, detail="Ошибка ввода данных"
            )

    except SQLAlchemyError as e:
        logger.error(f"ошибка в get_user: {str(e)}", exc_info=True)
        return JSONResponse(status_code=400, content={"result": "false", "error": str(e)})


@router.get(
    "/tweets",
    summary="Получение твитов",
    description="Получение твита - id, контент, ссылки на картинки, автор, и лайки",
    response_model=TweetRead,
    status_code=200,
)
async def get_tweets(request: Request,
        session: AsyncSession = Depends(db_helper.session_getter)
                       ):
    logger.info('Начался процесс получение твитов')
    try:
        api_key: str = request.headers.get("api-key")
        user_id = await get_user_id_by_api_key(session=session, api_key=api_key)
        if user_id:
            tweets=await get_tweets_info(session=session)
            logger.info(f'Получили в функцию get_tweets твиты {tweets}')
            return tweets
        else:
            logger.error(f"id={id} не найден")
            raise HTTPException(
                status_code=401, detail="Ошибка ввода данных"
            )


    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Ошибка в get_tweets. Детали: {error_message}")
        raise HTTPException(
            status_code=400, detail="Запрос не обработан. Ошибка на стороне сервера"
        )


@router.post("/tweets", response_model=TweetResponse)
async def create_tweet(
        request: Request,
        tweet_data: TweetCreate, session: AsyncSession = Depends(db_helper.session_getter)
                       ):
    try:
        logger.info('Начинаем процесс создание твита')
        api_key: str = request.headers.get("api-key")
        user_id = await get_user_id_by_api_key(session=session, api_key=api_key)
        if not user_id:
            logger.error(f"id={id} не найден")
            raise HTTPException(
                status_code=401, detail="Ошибка ввода данных"
            )
        tweet_id: int = await write_new_tweet(user_id=user_id, content=tweet_data.tweet_data, session=session)
        image_ids: list[int] = tweet_data.image_ids
        if image_ids:
            logger.info(f'обнаружены изображения {image_ids}')
            await update_tweet_with_media(
                    media_ids=image_ids, tweet_id=tweet_id, session=session
                    )
        logger.info('Твит добавлен')
        return {
            "result": True,
            "tweet_id": tweet_id
        }
    except SQLAlchemyError as e:
        logger.error(f"Error in create_tweet: {str(e)}", exc_info=True)
        return JSONResponse(status_code=400, content={"result": "false", "error": str(e)})

@router.post(
    "/medias",
    summary="Добавление изображения к твиту",
    description="Эндпоинт для добавления изображения к твиту",
    response_model=MediaRead,
    status_code=201,
)
async def post_media_with_tweet(
                        request:Request,
                        file: UploadFile = File(...),
                        session: AsyncSession = Depends(db_helper.session_getter)
                             ):
    try:
        api_key: str = request.headers.get("api-key")
        logger.info(f"Получен запрос POST MEDIA для API key: {api_key}")
        user_id = await get_user_id_by_api_key(session=session, api_key=api_key)
        if user_id:
            file_url = f"{api_key}_{file.filename}"
            media = await get_media(file_url=file_url, session=session)
            if media:
                return {"result": True, "media_id": media.id}
            else:
                media_id = await save_media(session=session, file=file, file_url=file_url, user_id=user_id)
                return {"result": True, "media_id": media_id}

        else:
                logger.error(f"id={id} не найден")
                raise HTTPException(
                    status_code=401, detail="Ошибка ввода данных"
            )

    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(
            f"POST запрос на /medias. Детали: {error_message}"
        )
        raise HTTPException(
            status_code=400, detail="Запрос не обработан. Ошибка на стороне сервера"
        )


@router.post(
    "/tweets/{id}/likes",
    summary="Добавление лайка к твиту с определенному ID",
    description="Пользователь ставит отметку «Нравится» на твит по ID",
    response_model=ResultBase,
    status_code=201,
)
async def post_like_to_tweet(
                        request:Request,
                        id: int,
                        session: AsyncSession = Depends(db_helper.session_getter)
                             ):
    try:
        api_key: str = request.headers.get("api-key")
        logger.info(f"Получен запрос POST LIKE для tweet ID: {id}, API key: {api_key}")
        user_id = await get_user_id_by_api_key(session=session, api_key=api_key)
        if user_id:
            tweet: Tweet = await get_tweet_by_id(session=session, tweet_id=id)
            if tweet:
                await add_like(user_id=user_id, tweet_id=id, session=session)
                logger.info(f'Выполнен запрос POST LIKE для tweet ID: {id}, user ID: {user_id}')
                return {"result": True}
            else:
                logger.error(f'Запрос POST LIKE для tweet ID: {id}, user ID: {user_id} не выполнен. Твит не найден')
        else:
            logger.error(f"id={id} не найден")
            raise HTTPException(
                status_code=401, detail="Ошибка ввода данных"
                )
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(
            f"POST запрос на /tweets/{id}/likes. Детали: {error_message}"
        )
        raise HTTPException(
            status_code=400, detail="Запрос не обработан. Ошибка на стороне сервера"
        )

@router.delete(
    "/tweets/{id}/likes",
    summary="Удаление лайка из твита, используя ID твита",
    description="Эндпоинт для удаления лайка",
    response_model=ResultBase,
    status_code=202,
)
async def delete_likes_from_tweet(request: Request,
                                  id: int,
                                  session: AsyncSession = Depends(db_helper.session_getter),
                                  ):
    try:
        api_key: str = request.headers.get("api-key")
        logger.info(f"Получен запрос DELETE Like для tweet ID: {id}, API key: {api_key}")
        user_id = await get_user_id_by_api_key(session=session, api_key=api_key)
        if user_id:
            tweet: Tweet = await get_tweet_by_id(session=session, tweet_id=id)
            if tweet:
                await delete_like(user_id=user_id, tweet_id=id, session=session)
                logger.info(f"Лайк удален")
                return {"result": True}
            else:
                logger.info(f'Пользователь id {id} не является автором твита. Удаление запрещено')
                raise HTTPException(
                    status_code=403,
                    detail="Ошибка на стороне сервера",
                )

        else:
            logger.error(f"id={id} не найден")
            raise HTTPException(
                status_code=401, detail="Ошибка ввода данных"
            )

    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(
            f"DELETE запрос на /tweets/{id}. Детали: {error_message}"
        )
        raise HTTPException(
            status_code=400, detail="Запрос не обработан. Ошибка на стороне сервера"
        )

@router.delete(
    "/tweets/{id}",
    summary="Удаление твита по ID",
    description="Endpoint по удалению твита. Твит удаляет его автор",
    response_model=ResultBase,
    status_code=202,
)
async def delete_tweet(request: Request,
                       id: int,
                       session: AsyncSession = Depends(db_helper.session_getter),
                       ):
    try:
        api_key: str = request.headers.get("api-key")
        logger.info(f"Получен запрос DELETE для tweet ID: {id}, API key: {api_key}")
        user_id = await get_user_id_by_api_key(session=session, api_key=api_key)
        if user_id:
            tweet: Tweet = await get_tweet_by_id(session=session, tweet_id=id)
            if tweet:
                if tweet.user_id == user_id:
                    await delete_like(user_id=user_id, tweet_id=id, session=session)
                    logger.info(f"Лайк удален")
                    await delete_tweet_by_id(tweet_id=id, session=session)
                    logger.info('Твит удален')
                    return {"result": True}
            else:
                logger.info(f'Пользователь id {id} не является автором твита. Удаление запрещено')
                raise HTTPException(
                    status_code=403,
                    detail="Ошибка на стороне сервера",
                )
        else:
            logger.error(f"id={id} не найден")
            raise HTTPException(
                status_code=401, detail="Ошибка ввода данных"
            )
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(
            f"DELETE запрос на /tweets/{id}. Детали: {error_message}"
        )
        raise HTTPException(
            status_code=400, detail="Запрос не обработан. Ошибка на стороне сервера"
        )


@router.post(
    "/users/{id}/follow",
    summary="Подписка на пользователя",
    description="Endpoint для предоставления возможности зафоловить другого пользователя",
    response_model=ResultBase,
    status_code=202,
)
async def post_follow_to_user(
        request: Request,
        id: int,
        session: AsyncSession = Depends(db_helper.session_getter),
):
    async with session.begin():
        try:
            # api_key = 'api123'
            api_key: str = request.headers.get("api-key")
            logger.info(f"Получен запрос POST FOLLOW для user ID: {id}, API key: {api_key}")

            follower_id = await get_user_id_by_api_key(session=session, api_key=api_key)
            if not follower_id:
                logger.error(f"id={id} не найден")
                raise HTTPException(status_code=401, detail="Ошибка ввода данных")

            is_already_following = await check_follow_user(
                user_id=follower_id,
                following_id=id,
                session=session
            )

            if is_already_following:
                logger.info(f"Пользователь {follower_id} уже подписан на {id}")
                raise HTTPException(
                    status_code=401,
                    detail="Запрос не обработан. Пользователь уже подписан"
                )

            success = await create_follow_to_user(
                follower_id=follower_id,
                following_id=id,
                session=session
            )

            if not success:
                logger.error(f"Ошибка создания подписки {follower_id} на {id}")
                raise HTTPException(status_code=500, detail="Ошибка создания подписки")

            return {"result": True}

        except SQLAlchemyError as e:
            await session.rollback()
            error_message = str(e)
            logger.error(f"POST запрос на /{id}/follow. Детали: {error_message}")
            raise HTTPException(
                status_code=400,
                detail="Запрос не обработан. Ошибка на стороне сервера"
            )

@router.delete(
"/users/{id}/follow",
    summary="Удаление подписки на другого пользователя",
    description="Endpoint по удалению подписки на другого пользователя",
    response_model=ResultBase,
    status_code=202,
)
async def delete_follow_from_user(
request: Request,
        id: int,
        session: AsyncSession = Depends(db_helper.session_getter),
):
    try:
        api_key: str = request.headers.get("api-key")
        logger.info(f"Получен запрос DELETE для user ID: {id}, API key: {api_key}")
        follower_id = await get_user_id_by_api_key(session=session, api_key=api_key)
        if not follower_id:
            logger.error(f"id={id} не найден")
            raise HTTPException(status_code=401, detail="Ошибка получения ID")
        is_already_following = await check_follow_user(
            user_id=follower_id,
            following_id=id,
            session=session
        )

        if is_already_following:
            logger.info(f"Пользователь {follower_id} подписан на {id}, подписка подтврждена")
            await delete_following_by_id(
                follower_id=follower_id,
                following_id=id,
                session=session
            )
            return {"result": True}
        else:
            logger.info(f"Пользователь {follower_id} не подписан на {id}, удаление невозможно")
            raise HTTPException(status_code=401, detail="Подписки не существует")

    except SQLAlchemyError as e:
        await session.rollback()
        error_message = str(e)
        logger.error(f"DELETE запрос на /{id}/follow. Детали: {error_message}")
        raise HTTPException(
            status_code=400,
            detail="Запрос не обработан. Ошибка на стороне сервера"
            )

