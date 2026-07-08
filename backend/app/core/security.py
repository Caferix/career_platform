import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from cryptography.fernet import Fernet
from slowapi import Limiter
from slowapi.util import get_remote_address

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

    def create_token(self, user_id: int, role: str, department: Optional[str] = None) -> str:
        """Kullanıcı için rol tabanlı JWT token üretir."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=60 * 24)  # 24 Saat geçerli
        to_encode = {
            "sub": str(user_id),
            "role": role,
            "exp": expire
        }
        if department:
            to_encode["department"] = department
            
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

auth = JWTAuth()

def hash_data(data: str) -> str:
    """
    Verilen metnin (Örn: telefon veya email) deterministik SHA-256 hash'ini üretir.
    Veritabanında hızlı arama yapmak (WHERE) için kullanılır.
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

# app/core/security.py dosyasının EN ALTINA eklenecek DOĞRU asenkron katman:

from fastapi import Header, HTTPException, status, Depends

async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Gelen isteklerin Header kısmındaki Bearer token'ı söker ve doğrular.
    Süresi dolmuşsa veya geçersizse anında 401 fırlatır.
    """
    try:
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Geçersiz token tipi."
            )
        
        # Token'ı gizli anahtar ile çözüyoruz
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload  # İçinde {"sub": "user_id", "role": "hr", "department": "Android"} dönecek
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum süresi dolmuş veya geçersiz token."
        )

async def require_hr(current_user: dict = Depends(get_current_user)) -> dict:
    """Sadece 'hr' rolüne sahip kullanıcıların geçmesine izin verir."""
    if current_user.get("role") != "hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user

async def require_manager(current_user: dict = Depends(get_current_user)) -> dict:
    """Sadece 'manager' rolüne sahip kullanıcıların geçmesine izin verir."""
    if current_user.get("role") != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user

async def require_hr_or_manager(current_user: dict = Depends(get_current_user)) -> dict:
    """Kullanıcı 'hr' veya 'manager' değilse geçişi engeller (403)."""
    if current_user.get("role") not in ["hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu alana erişim yetkiniz bulunmamaktadır."
        )
    return current_user