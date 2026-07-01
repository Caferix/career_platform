import os
# Pydantic v2 ile birlikte ayar yönetimi artık bu bağımsız paketten import edilir:
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 1. .env dosyasından okunacak hassas değişkenler ve Tipleri (Tip Güvenliği)
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    ENCRYPTION_KEY: str

    # 2. Kodda asla doğrudan yazılmaması gereken kurumsal sabitler
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRY_MINUTES: int = 3
    OTP_MAX_ATTEMPTS: int = 3
    
    # Dosya yükleme sınırları 
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB eder
    ALLOWED_EXTENSIONS: list = [".pdf", ".doc", ".docx"]

    # 3. Pydantic'e .env dosyamızın nerede durduğunu milimetrik tarif ediyoruz
    model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore"
)

# Diğer tüm dosyalar bu nesneyi çağırıp içindeki ayarları kullanacak
settings = Settings()