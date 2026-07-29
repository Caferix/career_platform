import logging
import httpx  # NetGSM HTTP API istekleri için asenkron istemci
from app.core.settings import settings

logger = logging.getLogger(__name__)

def _mask_phone(phone: str) -> str:
    """Kural 10: Log güvenliği için telefon numarasını maskeler (Örn: +90551***5838)"""
    if len(phone) >= 7:
        return f"{phone[:5]}***{phone[-4:]}"
    return "***"

async def send_sms(phone: str, code: str) -> bool:
    """
    Sadece SMS gönderme işini yapar (NetGSM altyapısı için yer tutucu içerir).
    Gevşek bağlılık (Loose Coupling) sağlar; yarın bir gün sağlayıcı 
    değişirse sadece bu fonksiyonun gövdesi güncellenir.
    """
    masked_phone = _mask_phone(phone)
    
    # 🎯 MOCK KALKANI: Eğer ayarlarda mock modu aktifse veya 
    # eski Twilio ayarları varsayılan değerde kalmışsa gerçek API'ye gitmeyi bloke et.
    sid_lower = settings.TWILIO_ACCOUNT_SID.lower()
    if settings.SMS_MOCK_MODE or "mock" in sid_lower or "acxxxx" in sid_lower:
        logger.info(f"[MOCK SMS] [{masked_phone}] İçerik: Giriş Kodunuz: {code}")
        return True

    # 🚀 NETGSM ALTYAPISI HAZIR (Şirket canlı bilgileri girince burası aktifleşecek)
    # NetGSM endpoint'i ve payload şeması hazırlandı.
    url = "https://api.netgsm.com.tr/sms/send/post/v2"
    payload = {
        "user": settings.NETGSM_USER,
        "password": settings.NETGSM_PASSWORD,
        "gsm": phone,
        "text": f"Dener Kariyer Platformu Giriş Kodunuz: {code}. Bu kod {settings.OTP_EXPIRY_MINUTES} dakika geçerlidir.",
        "header": settings.NETGSM_HEADER,
        "filter": "0"
    }

    try:
        # Not: httpx asenkron çalıştığı için FastAPI event loop'unu bloklamaz.
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            
            # Başarılı gönderim kontrolü (NetGSM HTTP statüsü 200 döner ve body'de hata kodu yazar)
            if response.status_code == 200 and "00" in response.text:
                logger.info(f"NetGSM SMS gönderildi: {masked_phone}")
                return True
            else:
                logger.warning(f"NetGSM SMS gönderilemedi! Status: {response.status_code}, Body: {response.text}")
                return False
            
    except Exception as e:
        logger.error(f"NetGSM SMS gönderim hatası ({masked_phone}): {str(e)}")
        return False