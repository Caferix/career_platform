from sqlalchemy.ext.asyncio import AsyncSession
from app.models.security_models import AccessLog

async def log_access(
    db: AsyncSession, 
    user_id: int, 
    user_role: str, 
    action: str, 
    target_id: int, 
    ip_address: str
) -> AccessLog:
    """
    İK veya Departman Yöneticilerinin hassas verilere (Örn: CV indirme, statü değiştirme)
    erişimini ve yaptığı işlemleri veritabanına mühürler. KVKK gereği silme operasyonu içermez.
    """
    db_log = AccessLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        target_id=target_id,
        ip_address=ip_address
    )
    db.add(db_log)
    await db.commit()
    return db_log