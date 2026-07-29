import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import SessionLocal
from app.schemas.user import UserCreate
from app.services import user as user_service
from app.core.settings import settings

async def seed():
    async with SessionLocal() as db:
        # .env / settings içerisinden admin bilgilerini güvenli bir şekilde alıyoruz
        admin_name = getattr(settings, "ADMIN_LOGIN", None)
        admin_password = getattr(settings, "ADMIN_PASSWORD", None)

        if not admin_name or not admin_password:
            print("❌ HATA: .env dosyasında ADMIN_LOGIN veya ADMIN_PASSWORD okunamadı!")
            return

        # db.query() yasak, asenkron get_user_by_login_name servisimiz select() ile kontrol ediyor
        existing_admin = await user_service.get_user_by_login_name(db, admin_name)
        if not existing_admin:
            # Rotalar ince, iş servislerde. Kayıt işlemini asenkron servise paslıyoruz.
            await user_service.create_user(
                db=db,
                payload=UserCreate(
                    login_name=admin_name, 
                    password=admin_password, 
                    role="admin",
                    department=None
                )
            )
            print(f"✅ Başarılı: Sistem ilk kurulumu yapıldı. ADMIN kullanıcısı mühürlendi -> {admin_name}")
        else:
            print("ℹ️ ADMIN kullanıcısı veritabanında zaten mevcut, tohumlama atlanıyor.")

if __name__ == "__main__":
    asyncio.run(seed())