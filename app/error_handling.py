from functools import wraps
from typing import Any, Callable, Awaitable
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from app.config import logger


def handle_api_errors():
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]: #Corrected Callable usage
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "result": False,
                        "error_type": "AuthenticationError",
                        "error_message": str(e.detail),
                    },
                )
            except SQLAlchemyError as e:
                logger.error(f"Database error: {str(e)}", exc_info=True)  #Improved message
                return JSONResponse(
                    status_code=400,
                    content={
                        "result": False,
                        "error_type": "DatabaseError",
                        "error_message": str(e),
                    },
                )
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}", exc_info=True) #Improved message
                return JSONResponse(
                    status_code=500,
                    content={
                        "result": False,
                        "error_type": e.__class__.__name__,
                        "error_message": str(e),
                    },
                )

        return wrapper

    return decorator

