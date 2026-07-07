from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_models import AccessLog


async def log_access(
    db: AsyncSession,
    user_id: int,
    user_role: str,
    action: str,
    target_id: int | None,
    ip_address: str | None,
) -> AccessLog:
    access_log = AccessLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        target_id=target_id,
        ip_address=ip_address,
    )
    db.add(access_log)
    await db.commit()
    await db.refresh(access_log)
    return access_log