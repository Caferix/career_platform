from cryptography.fernet import Fernet
from app.core.settings import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

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