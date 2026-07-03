import logging
from twilio.rest import Client
from app.core.settings import settings

logger = logging.getLogger(__name__)

def _mask_phone(phone: str) -> str:
    """Kural 10: Log güvenliği için telefon numarasını maskeler (Örn: +90551***5838)"""
    if len(phone) >= 7:
        return f"{phone[:5]}***{phone[-4:]}"
    return "***"

async def send_sms(phone: str, code: str) -> bool:
    """Sadece SMS gönderme işini yapar."""
    masked_phone = _mask_phone(phone)
    
    
    # Küçük/büyük harf duyarlılığını kaldırıyoruz ve içinde 'acxxx' (varsayılan değer) 
    # veya 'mock' geçen her durumda gerçek Twilio'ya gitmeyi bloke ediyoruz.
    sid_lower = settings.TWILIO_ACCOUNT_SID.lower()
    if "mock" in sid_lower or "acxxxx" in sid_lower:
        logger.info(f"[MOCK SMS] [{masked_phone}] İçerik: Giriş Kodunuz: {code}")
        return True

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Dener Kariyer Platformu Giriş Kodunuz: {code}. Bu kod {settings.OTP_EXPIRY_MINUTES} dakika geçerlidir.",
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone
        )
        logger.info(f"SMS başarıyla gönderildi. SID: {message.sid} -> Alıcı: {masked_phone}")
        return True

    except Exception as e:
        logger.error(f"SMS gönderim hatası ({masked_phone}): {str(e)}")
        return False