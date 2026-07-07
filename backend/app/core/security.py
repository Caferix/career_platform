import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

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
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.ALGORITHM

    def create_token(
        self,
        user_id: int,
        role: str,
        department: Optional[str] = None,
        expires_delta: Optional[timedelta] = None,
        extra_claims: Optional[dict] = None,
    ) -> str:
        """Kullanıcı için rol tabanlı JWT token üretir."""
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS))
        to_encode = {
            "user_id": user_id,
            "role": role,
            "exp": expire
        }
        if department:
            to_encode["department"] = department
        if extra_claims:
            to_encode.update(extra_claims)
            
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

auth = JWTAuth()

def hash_data(data: str) -> str:
    """
    Verilen metnin (Örn: telefon veya email) deterministik SHA-256 hash'ini üretir.
    Veritabanında hızlı arama yapmak (WHERE) için kullanılır.
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

# Gelen isteklerin Header kısmındaki "Authorization: Bearer <token>" yapısını söker
async def get_current_user(authorization: str = Header(default=None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kimlik doğrulama bilgisi eksik."
        )

    try:
        token_type, token = authorization.split(" ", 1)
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token tipi.")

        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token."
        )


async def get_current_user_token_data(authorization: str = Header(default=None)) -> dict:
    return await get_current_user(authorization)


async def require_hr(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user


async def require_manager(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user


async def require_hr_or_manager(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") not in {"hr", "manager"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )
    return current_user
    

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, token_data: dict = Depends(get_current_user)):
        user_role = token_data.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz bulunmamaktadır."
            )
        return token_data
