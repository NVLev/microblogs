from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from app.config import logger
from app.db_helper import db_helper
from app.error_handling import handle_api_errors

router = APIRouter(prefix="", tags=["Работа с микроблогами"])


@router.get("/")
@handle_api_errors()
async def get_index(session: AsyncSession = Depends(db_helper.session_getter)):
    with open("./templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)
