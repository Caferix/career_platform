# app/routes/auth.py
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db  
from app.schemas.auth import SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.schemas.user import LoginRequest  
from app.services import sms, otp
from app.services import user as user_service  # Asenkron servis katmanı
from app.core.security import limiter, auth, hash_data
from app.services import candidate as candidate_service
from app.models.auth_log import FailedLoginAttempt

# Router tanımını yapıyoruz. main.py'de prefix="/auth" olarak bağlanacağı için 
# altındaki rotaların path'lerini buna göre güncelliyoruz.
router = APIRouter()

# --- 1. GERÇEK VERİTABANI BAĞLANTILI ADMİN GİRİŞ ENDPOINT'İ ---
@router.post("/login", response_model=TokenResponse) # 🌟 response_model geri geldi!
@limiter.limit("5/minute")
async def admin_login(
    request: Request, 
    payload: LoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Admin, HR ve Departman Yöneticileri için Güvenli Kurumsal Giriş Kapısı.
    Şemaya tam uyumlu veri döner ve hatalı girişleri asenkron loglar.
    """
    user = await user_service.authenticate_user(
        db=db, 
        login_name=payload.login_name, 
        password=payload.password
    )
    
    # 🌟 Başarısız giriş brute-force kaydı
    if not user:
        failed_attempt = FailedLoginAttempt(
            login_name=payload.login_name,
            ip_address=request.client.host or "0.0.0.0"
        )
        db.add(failed_attempt)
        await db.commit()

        # Kural 8 & 19: Güvenlik sızıntısı vermemek için jenerik hata mesajı
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )
    
    access_token = auth.create_token(
        user_id=user.id, 
        role=user.role,
        department=user.department
    )
    
    # 🌟 Artık Pydantic şeması (TokenResponse) tarafından doğrulanarak güvenle döner
    return TokenResponse(
        access_token=access_token, 
        token_type="bearer",
        role=user.role,
        department=user.department
    )


# --- 2. ADAY OTP GÖNDERME ENDPOINT'İ ---
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


# --- 3. ADAY OTP DOĞRULAMA ENDPOINT'İ ---
@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit("5/minute")
async def verify_otp(request: Request, payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Gelen OTP kodunu doğrular. Başarılı ise 'Gölge Aday' oluşturup
    'phone_verification' rızasını mühürler ve JWT Access Token üretir.
    """
    is_valid = await otp.verify_otp(db, phone=payload.phone, code=payload.code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş doğrulama kodu."
        )
        
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")

    # Gölge aday servisini çağırıyoruz
    candidate_id = await candidate_service.get_or_create_shadow_candidate(
        db=db,
        phone=payload.phone,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # sub alanı ve veritabanı araması için aynı hash fonksiyonunu kullanıyoruz
    hashed_phone = hash_data(payload.phone)

    access_token = auth.create_token(
        user_id=candidate_id,  # Gerçek veritabanı ID'si token'a gömüldü!
        role="applicant",
        department=None,
        sub=hashed_phone
    )
    
    return TokenResponse(access_token=access_token, token_type="bearer")