import random
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.security_models import OTPRecord
from app.core.security import encrypt_data, decrypt_data  # decrypt_data fonksiyonunu ekledik
from app.core.settings import settings

logger = logging.getLogger(__name__)

def generate_otp() -> str:
    """6 haneli güvenli OTP kodu üretir."""
    return str(random.randint(100000, 999999))

async def save_otp(db: AsyncSession, phone: str, code: str) -> OTPRecord:
    """Kullanıcının telefon numarasını şifreleyerek yeni bir OTP kaydını veritabanına yazar."""
    encrypted_phone = encrypt_data(phone)
    
    # Windows-Docker saat senkronizasyonu için timezone-aware (saf UTC) yapıyoruz
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    otp_record = OTPRecord(
        phone=encrypted_phone,
        code=code,
        expires_at=expires_at,
        attempt_count=0,
        is_used=False
    )
    
    db.add(otp_record)
    await db.commit()
    await db.refresh(otp_record)
    return otp_record

async def verify_otp(db: AsyncSession, phone: str, code: str) -> bool:
    """OTP doğrulama iş mantığı zinciri."""
    
    # 🎯 ÇÖZÜM: Fernet her seferinde farklı şifre ürettiği için WHERE ile telefon eşleyemeyiz.
    # Son üretilen aktif/yarı-aktif son 20 kaydı çekip, kod içinde deşifre ederek eşleştiriyoruz.
    query = (
        select(OTPRecord)
        .order_by(OTPRecord.id.desc())
        .limit(20)
    )
    result = await db.execute(query)
    otp_records = result.scalars().all()
    
    # Gelen telefona ait en güncel kaydı bulalım
    target_record = None
    for record in otp_records:
        try:
            # DB'deki şifreli telefonu çözüp gelen telefonla karşılaştırıyoruz
            decrypted_phone = decrypt_data(record.phone)
            if decrypted_phone == phone:
                target_record = record
                break  # En güncel olanı bulduğumuz için döngüden çıkıyoruz
        except Exception:
            continue

    # Eğer bu telefona ait hiçbir kod üretilmemişse direkt reddet
    if not target_record:
        logger.warning(f"Doğrulama başarısız: Telefon numarasına ait OTP kaydı bulunamadı.")
        return False
        
    # Windows/Docker saat dilimi karmaşasını önlemek için 'naive' UTC kıyaslaması
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Güvenlik Kontrolü 1: Kod daha önce kullanıldıysa veya süresi dolduysa iptal
    if target_record.is_used or now > target_record.expires_at.replace(tzinfo=None):
        logger.warning(f"Doğrulama başarısız: Kod kullanılmış veya süresi dolmuş. Sınır: {target_record.expires_at}, Şu an: {now}")
        return False
        
    # Güvenlik Kontrolü 2: Maksimum deneme sınırı aşıldıysa direkt reddet
    if target_record.attempt_count >= settings.OTP_MAX_ATTEMPTS:
        logger.warning(f"Doğrulama başarısız: Maksimum deneme sınırı ({settings.OTP_MAX_ATTEMPTS}) aşıldı.")
        return False
        
    # Kod Eşleşme Kontrolü
    if target_record.code == code:
        target_record.is_used = True
        await db.commit()
        logger.info(f"OTP başarıyla doğrulandı.")
        return True
    else:
        target_record.attempt_count += 1
        await db.commit()
        logger.warning(f"Doğrulama başarısız: Hatalı OTP kodu girildi. Deneme: {target_record.attempt_count}")
        return False