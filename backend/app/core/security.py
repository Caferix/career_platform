import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from cryptography.fernet import Fernet
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from app.core.settings import settings

# .env içindeki ENCRYPTION_KEY ile kriptolama motorunu başlatıyoruz
fernet = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    if data is None:
        return None
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    if encrypted_data is None:
        return None
    return fernet.decrypt(encrypted_data.encode()).decode()

limiter = Limiter(key_func=get_remote_address)

# 1. Şifre Hashleme ve Doğrulama (SHA-256)
def hash_password(password: str) -> str:
    """
    Ham şifreyi SHA-256 ile hashler ve geriye OKUNABİLİR 
    64 karakterli bir HEXADECIMAL STRING döner.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Dışarıdan gelen ham şifreyi hashler ve DB'deki (veya mock sözlükteki)
    string hash ile constant-time (güvenli) olarak kıyaslar.
    """
    plain_hash = hash_password(plain_password)
    
    # İki taraf da kesinlikle string (str) olduğu için güvenle byte'a çevirip hmac'e veriyoruz
    return hmac.compare_digest(plain_hash.encode("utf-8"), hashed_password.encode("utf-8"))


# 2. JWT Token Yönetimi
class JWTAuth:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM

    def create_token(self, user_id: int, role: str, department: str = None, sub: str = None) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": sub or str(user_id),
            "user_id": user_id,
            "role": role,
            "exp": expire
        }
        if department:
            payload["department"] = department
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

auth = JWTAuth()

def hash_data(data: str) -> str:
    """
    Verilen metnin (Örn: telefon veya email) deterministik SHA-256 hash'ini üretir.
    Veritabanında hızlı arama yapmak (WHERE) için kullanılır.
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()



security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        # İç detay vermeden standart hata
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum süresi dolmuş veya geçersiz token."
        )

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Sadece tam yetkili 'admin' rolüne sahip kullanıcıların geçmesine izin verir."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user

async def require_hr(current_user: dict = Depends(get_current_user)) -> dict:
    """Sadece 'hr' veya üstü ('admin') rolüne sahip kullanıcıların geçmesine izin verir."""
    if current_user.get("role") not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user

async def require_manager(current_user: dict = Depends(get_current_user)) -> dict:
    """Sadece 'manager' veya üstü ('admin') rolüne sahip kullanıcıların geçmesine izin verir."""
    if current_user.get("role") not in ["manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user

async def require_hr_or_manager(current_user: dict = Depends(get_current_user)) -> dict:
    """Kullanıcı 'hr', 'manager' veya 'admin' değilse geçişi engeller."""
    if current_user.get("role") not in ["hr", "manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu alana erişim yetkiniz bulunmamaktadır."
        )
    return current_user