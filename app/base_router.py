from typing import Annotated
from starlette.responses import HTMLResponse
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status

)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)



from app.db_helper import db_helper
from app.config import logger

router = APIRouter(prefix='', tags=['Работа с микроблогами'])

@router.get("/")
async def get_index(session: AsyncSession = Depends(db_helper.session_getter)):
    try:
        with open("./templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template file not found"
        )
    except Exception as e:
        logger.error(f"Error reading template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
# @router.post("/create_user", response_model=UserCreate)
# async def create_new_user(
#         session: Annotated[
#         AsyncSession,
#         Depends(db_helper.session_getter),
#     ],
#         user_create: UserCreate):
#     try:
#         user = await create_user(
#             session=session,
#             user_create=user_create,
#         )
#         return user
#     except Exception as e:
#         logger.error(f"Error creating recipe: {e}")
#         raise