from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db  # Projendeki db session yield fonksiyonu
from app.schemas.auth import SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.services import sms, otp, auth
from app.core.security import limiter

router = APIRouter()

@router.post("/send-otp", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def send_otp(request: Request, payload: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Kullanıcının telefonuna 6 haneli tek kullanımlık doğrulama kodu (OTP) gönderir.
    """
    # 1. 6 Haneli rastgele kod üret
    code = otp.generate_otp()
    
    # 2. Kodu veritabanına şifreli olarak kaydet
    await otp.save_otp(db, phone=payload.phone, code=code)
    
    # 3. SMS servislerini tetikle (Twilio entegrasyonu)
    sms_sent = await sms.send_sms(phone=payload.phone, code=code)
    
    if not sms_sent:
        # Kural 8: İç detayı sızdırmadan genel bir hata fırlatıyoruz
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doğrulama kodu gönderilemedi. Lütfen daha sonra tekrar deneyin."
        )
        
    return {"message": "Doğrulama kodu başarıyla gönderildi."}


@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit("5/minute")
async def verify_otp(request: Request, payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Gelen OTP kodunu doğrular. Başarılı ise rol tabanlı JWT Access Token üretir.
    """
    # 1. OTP servisinden doğrulama zincirini işlet
    is_valid = await otp.verify_otp(db, phone=payload.phone, code=payload.code)
    
    if not is_valid:
        # Kural 8: Kodun süresi mi doldu, deneme hakkı mı bitti detay vermiyoruz!
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş doğrulama kodu."
        )
        
    # 2. Doğrulama başarılı! Şimdilik sahte bir user_id (örn: 1) ile token üretiyoruz.
    # (Faz 4 ve 5'te burası gerçek kullanıcı/aday ID'si ile yer değiştirecek)
    access_token = auth.create_token(user_id=1, role="applicant")
    
    return TokenResponse(access_token=access_token, token_type="bearer")