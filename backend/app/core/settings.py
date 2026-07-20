import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

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

    # Twilio sabitleri
    TWILIO_ACCOUNT_SID: str = "mock_sid"
    TWILIO_AUTH_TOKEN: str = "mock_token"
    TWILIO_FROM_NUMBER: str = "+1234567890"
    
    # Dosya yükleme sınırları 
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB eder
    ALLOWED_EXTENSIONS: list = [".pdf", ".doc", ".docx"]

    # JWT İmzalama
    SECRET_KEY: str = "mock_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # SMS Mock Kontrolü
    SMS_MOCK_MODE: bool = True

    # backend/uploads/ klasör yolunu projenin kök dizinine göre dinamik oluşturur
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

    # Maksimum dosya boyutu 5MB
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  

    # Güvenlik kuralı: Sadece izin verilen döküman formatları
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx"]

    BASE_URL: str = "http://localhost:8000"

    SEED_HR_LOGIN: str = "hr_admin"
    SEED_HR_PASSWORD: str = ""
    SEED_MANAGER_LOGIN: str = "manager_admin"
    SEED_MANAGER_PASSWORD: str = ""
    SEED_MANAGER_DEPARTMENT: str = "Yazılım Geliştirme"
   


    # 3. Pydantic'e .env dosyamızın nerede durduğunu milimetrik tarif ediyoruz
    model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore"
)

# Diğer tüm dosyalar bu nesneyi çağırıp içindeki ayarları kullanacak
settings = Settings()