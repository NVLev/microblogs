from functools import wraps
from typing import Any, Dict, Callable
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from config import logger


def handle_api_errors():
    def decorator(func: Callable) -> Callable:
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
                        "error_message": str(e.detail)
                    }
                )
            except SQLAlchemyError as e:
                logger.error(f"Ошибка базы данных: {str(e)}", exc_info=True)
                return JSONResponse(
                    status_code=400,
                    content={
                        "result": False,
                        "error_type": "DatabaseError",
                        "error_message": str(e)
                    }
                )
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
                return JSONResponse(
                    status_code=500,
                    content={
                        "result": False,
                        "error_type": e.__class__.__name__,
                        "error_message": str(e)
                    }
                )
        return wrapper
    return decorator