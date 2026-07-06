import hashlib
import secrets 
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.security_models import OTPRecord
from app.core.security import encrypt_data, decrypt_data
from app.core.settings import settings

logger = logging.getLogger(__name__)

def generate_otp() -> str:
    """
    Kriptografik olarak güvenli 6 haneli OTP kodu üretir.
    Saldırganlar tarafından tahmin edilemez.
    """
    # secrets.randbelow(900000) -> 0 ile 899999 arasında sayı üretir.
    # Üzerine 100000 ekleyerek her zaman 6 haneli (100000 - 999999) kalmasını garanti ederiz.
    return str(secrets.randbelow(900000) + 100000)

async def save_otp(db: AsyncSession, phone: str, code: str) -> OTPRecord:
    """Telefon numarasını şifreleyerek UTC zaman damgalı yeni OTP kaydı oluşturur."""
    encrypted_phone = encrypt_data(phone)
    hashed_phone = hashlib.sha256(phone.encode()).hexdigest()  # arama için
    
   
    # Zaman yönetimi tamamen UTC-aware (saat dilimi bilgisi içeren) standartta.
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    otp_record = OTPRecord(
        phone=encrypted_phone,
        hashed_phone = hashed_phone,
        code=code,
        expires_at=expires_at,  # Model katmanında bu alan DateTime(timezone=True) olmalı
        attempt_count=0,
        is_used=False
        

    )
    
    db.add(otp_record)
    await db.commit()
    await db.refresh(otp_record)
    return otp_record

async def verify_otp(db: AsyncSession, phone: str, code: str) -> bool:
    now = datetime.now(timezone.utc)
    hashed_phone = hashlib.sha256(phone.encode()).hexdigest()
    
    query = (
        select(OTPRecord)
        .where(
            and_(
                OTPRecord.hashed_phone == hashed_phone,
                OTPRecord.is_used == False,
                OTPRecord.expires_at >= now
            )
        )
        .order_by(OTPRecord.id.desc())
        .limit(1)
    )
    
    result = await db.execute(query)
    target_record = result.scalar_one_or_none()
    
    if not target_record:
        logger.warning(f"Aktif OTP yok: {phone[:4]}***")
        return False
    
    if target_record.attempt_count >= settings.OTP_MAX_ATTEMPTS:
        logger.warning(f"Max deneme aşıldı: {phone[:4]}***")
        return False
    
    if target_record.code == code:
        target_record.is_used = True
        await db.commit()
        logger.info("OTP doğrulandı.")
        return True
    else:
        target_record.attempt_count += 1
        await db.commit()
        logger.warning(f"Hatalı OTP. Deneme: {target_record.attempt_count}")
        return False