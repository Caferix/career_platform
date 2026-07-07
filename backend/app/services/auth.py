from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from app.core.settings import settings

def create_token(
    user_id: int,
    role: str = "applicant",
    department: str | None = None,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Kullanıcıya özel, rol tabanlı ve süreli bir JWT access_token üretir.
    """
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS))
    
    # Biletin içine gömülecek veriler (Claims)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expire
    }
    if department:
        payload["department"] = department
    if extra_claims:
        payload.update(extra_claims)
    
    # .env'deki gizli anahtar ve algoritma ile imzala
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict | None:
    """
    Gelen JWT biletinin imzasını ve süresini kontrol eder.
    Bilet geçerliyse içindeki payload sözlüğünü döner, geçersizse None döner.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        # Kural 8: Hata detayları (imza geçersiz, süre dolmuş vb.) dışarı sızdırılmaz
        return None