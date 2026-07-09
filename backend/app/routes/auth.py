# app/routes/auth.py
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db  
from app.schemas.auth import SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.schemas.user import LoginRequest  # Yeni eklediğimiz şema
from app.services import sms, otp
from app.services import user as user_service  # Yeni asenkron servis katmanımız
from app.core.security import limiter, auth

# Router tanımını yapıyoruz. main.py'de prefix="/auth" olarak bağlanacağı için 
# altındaki rotaların path'lerini buna göre güncelliyoruz.
router = APIRouter()

# --- 1. GERÇEK VERİTABANI BAĞLANTILI ADMİN GİRİŞ ENDPOINT'İ ---
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def admin_login(
    request: Request, 
    payload: LoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    HR ve Departman Yöneticileri için Güvenli Kurumsal Giriş Kapısı.
    Girişler tamamen login_name ve asenkron şifre doğrulaması ile veritabanından yapılır.
    """
    #  Mock DB tamamen kaldırıldı, asenkron veritabanı doğrulama servisi çağrılıyor
    user = await user_service.authenticate_user(
        db=db, 
        login_name=payload.login_name, 
        password=payload.password
    )
    
    # Kural 8: Güvenlik sızıntısı vermemek için jenerik hata mesajı
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )
    
    # Başarılı girişte kullanıcının gerçek id, role ve department bilgileri JWT payload'una gömülür
    access_token = auth.create_token(
        user_id=user.id, 
        role=user.role,
        department=user.department
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


# --- 2. ADAY OTP GÖNDERME ENDPOINT'İ (DEĞİŞMEDİ - KORUNDU) ---
@router.post("/send-otp", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def send_otp(request: Request, payload: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Kullanıcının telefonuna 6 haneli tek kullanımlık doğrulama kodu (OTP) gönderir.
    """
    if not payload.kvkk_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="KVKK onayı olmadan işlem yapılamaz."
        )

    # 1. 6 Haneli rastgele kod üret
    code = otp.generate_otp()
    
    # 2. Kodu veritabanına şifreli olarak kaydet
    await otp.save_otp(db, phone=payload.phone, code=code)
    
    # 3. SMS servislerini tetikle
    sms_sent = await sms.send_sms(phone=payload.phone, code=code)
    
    if not sms_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doğrulama kodu gönderilemedi. Lütfen daha sonra tekrar deneyin."
        )
        
    return {"message": "Doğrulama kodu başarıyla gönderildi."}


# --- 3. ADAY OTP DOĞRULAMA ENDPOINT'İ (DEĞİŞMEDİ - KORUNDU) ---
@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit("5/minute")
async def verify_otp(request: Request, payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Gelen OTP kodunu doğrular. Başarılı ise rol tabanlı JWT Access Token üretir.
    """
    # 1. OTP servisinden doğrulama zincirini işlet
    is_valid = await otp.verify_otp(db, phone=payload.phone, code=payload.code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş doğrulama kodu."
        )
        
    # Doğrulama başarılı! Aday için hashed_phone'u sub olarak token'a göm
    hashed_phone = hashlib.sha256(payload.phone.encode()).hexdigest()

    access_token = auth.create_token(
        user_id=0,           # aday henüz kayıtlı olmayabilir
        role="applicant",
        department=None,
        sub=hashed_phone     # /applicants/me bunu kullanacak
)
    
    return TokenResponse(access_token=access_token, token_type="bearer")