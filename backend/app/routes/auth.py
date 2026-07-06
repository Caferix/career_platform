from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db  # Projendeki db session yield fonksiyonu
from app.schemas.auth import AdminLoginRequest, SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.services import sms, otp, auth
from app.core.security import limiter, verify_password

router = APIRouter()

# --- KURUMSAL ADMİN VERİTABANI (MOCK) ---
MOCK_ADMIN_DB = {
    "hr_admin": {
        "role": "hr",
        "user_id": 99,
        "hashed_password": "0c8771368cbc0744465bf202b5d3dac72ff829ed0edb2922cf089426b12b9380"  # SuperSecretHR123
    },
    "manager_admin": {
        "role": "manager",
        "user_id": 100,
        "hashed_password": "648d38b0699e3e8022c40ef7a1794ee79a7adb8ccf274dc2730866cd37b72504"  # ManagerPass321
    }
}

# --- 1. ADMİN GİRİŞ ENDPOINT'İ ---
@router.post("/admin/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def admin_login(request: Request, payload: AdminLoginRequest):
    """
    HR ve Departman Yöneticileri için Güvenli Kurumsal Giriş Kapısı.
    Girişler tamamen login_name ve SHA-256 şifre hash'i ile yapılır.
    """
    # Gelen isteği login_name alanıyla aratıyoruz, mail kelimesi tamamen temizlendi
    user_info = MOCK_ADMIN_DB.get(payload.login_name)
    
    if user_info and verify_password(payload.password, user_info["hashed_password"]):
        access_token = auth.create_token(user_id=user_info["user_id"], role=user_info["role"])
        return TokenResponse(access_token=access_token, token_type="bearer")
    else:
        # Kural 8: Güvenlik sızıntısı vermemek için jenerik hata mesajı
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )

# --- 2. ADAY OTP GÖNDERME ENDPOINT'İ ---
@router.post("/send-otp", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def send_otp(request: Request, payload: SendOTPRequest, db: AsyncSession = Depends(get_db)):

# Kullanıcı onay vermediyse alt satırlara hiç geçmeden burada kapıyı kapatıyoruz.
    if not request.kvkk_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="KVKK onayı olmadan işlem yapılamaz."
        )

    """
    Kullanıcının telefonuna 6 haneli tek kullanımlık doğrulama kodu (OTP) gönderir.
    """
    # 1. 6 Haneli rastgele kod üret
    code = otp.generate_otp()
    
    # 2. Kodu veritabanına şifreli olarak kaydet
    await otp.save_otp(db, phone=payload.phone, code=code)
    
    # 3. SMS servislerini tetikle (Mock veya NetGSM/Twilio altyapısı)
    sms_sent = await sms.send_sms(phone=payload.phone, code=code)
    
    if not sms_sent:
        # Kural 8: İç detayı sızdırmadan genel bir hata fırlatıyoruz
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doğrulama kodu gönderilemedi. Lütfen daha sonra tekrar deneyin."
        )
        
    return {"message": "Doğrulama kodu başarıyla gönderildi."}

# --- 3. ADAY OTP DOĞRULAMA ENDPOINT'İ ---
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