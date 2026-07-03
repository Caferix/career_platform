import random
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.security_models import OTPRecord  # Projendeki model adıyla eşleşmeli
from app.core.security import encrypt_data
from app.core.settings import settings

def generate_otp() -> str:
    """6 haneli güvenli OTP kodu üretir."""
    return str(random.randint(100000, 999999))

async def save_otp(db: AsyncSession, phone: str, code: str) -> OTPRecord:
    """
    Kullanıcının telefon numarasını şifreleyerek 
    yeni bir OTP kaydını veritabanına yazar.
    """
    # KVKK Güvenliği: Telefon numarası ham haliyle DB'ye gidemez
    encrypted_phone = encrypt_data(phone)
    
    # Geçerlilik süresi hesaplama (Mevcut zaman + 3 dakika)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
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
    """
    OTP doğrulama iş mantığı zinciri.
    Şifreli telefona ait en güncel kodu bulur ve kuralları denetler.
    """
    # Sorgulama yapabilmek için gelen ham telefonu da aynı algoritmayla şifreliyoruz
    encrypted_phone = encrypt_data(phone)
    
    # Kural 4: Veritabanından bu telefona ait EN SON üretilen kaydı çekiyoruz
    query = (
        select(OTPRecord)
        .where(OTPRecord.phone == encrypted_phone)
        .order_by(OTPRecord.id.desc())
        .limit(1)
    )
    result = await db.execute(query)
    otp_record = result.scalar_one_or_none()
    
    # Eğer bu telefona ait hiçbir kod üretilmemişse direkt reddet
    if not otp_record:
        return False
        
    # Güvenlik Kontrolü 1: Kod daha önce kullanıldıysa veya süresi dolduysa iptal
    if otp_record.is_used or datetime.utcnow() > otp_record.expires_at:
        return False
        
    # Güvenlik Kontrolü 2: Maksimum deneme sınırı aşıldıysa direkt reddet
    if otp_record.attempt_count >= settings.OTP_MAX_ATTEMPTS:
        return False
        
    # Kod Eşleşme Kontrolü
    if otp_record.code == code:
        # Kod doğruysa tek kullanımlık hale getir (is_used = True)
        otp_record.is_used = True
        await db.commit()
        return True
    else:
        # Kod yanlışsa deneme sayacını 1 artır ve kilitlemeye yaklaştır
        otp_record.attempt_count += 1
        await db.commit()
        return False