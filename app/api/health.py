from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Application health check",
)
async def health_check() -> dict[str, str]:
    """Check if the application is running."""
    return {"status": "ok"}


@router.get(
    "/health/db",
    summary="Database health check",
)
async def database_health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Check database connectivity."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
