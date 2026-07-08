# backend/seed_users.py

import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import SessionLocal
from app.schemas.user import UserCreate
from app.services import user as user_service
# 🌟 .env dosyasını otomatik yüklemek için projenin kendi settings nesnesini import ediyoruz
from app.core.settings import settings

async def seed():
    async with SessionLocal() as db:
        hr_name     = settings.SEED_HR_LOGIN
        hr_password = settings.SEED_HR_PASSWORD
        manager_name = settings.SEED_MANAGER_LOGIN
        manager_password = settings.SEED_MANAGER_PASSWORD
        manager_dept = settings.SEED_MANAGER_DEPARTMENT

        # Eğer üstteki os.getenv'ler null dönerse, settings nesnesi üzerinden doğrudan fallback yapıyoruz
        if not hr_password or not manager_password:
            # Pydantic Settings .env'yi okuduğu için burası can simidimiz olacak
            hr_password = getattr(settings, "SEED_HR_PASSWORD", None)
            manager_password = getattr(settings, "SEED_MANAGER_PASSWORD", None)

        if not hr_password or not manager_password:
            print("❌ HATA: .env dosyasında SEED_HR_PASSWORD veya SEED_MANAGER_PASSWORD hâlâ okunamadı!")
            return

        # 1. HR Kullanıcısı Kontrol ve Tohumlama
        existing_hr = await user_service.get_user_by_login_name(db, hr_name)
        if not existing_hr:
            await user_service.create_user(
                db=db,
                payload=UserCreate(
                    login_name=hr_name, 
                    password=hr_password, 
                    role="hr"
                )
            )
            print(f"✅ Başarılı: HR kullanıcısı sisteme mühürlendi -> {hr_name}")
        else:
            print("ℹ️ HR kullanıcısı veritabanında zaten mevcut, atlanıyor.")

        # 2. Manager Kullanıcısı Kontrol ve Tohumlama
        existing_mgr = await user_service.get_user_by_login_name(db, manager_name)
        if not existing_mgr:
            await user_service.create_user(
                db=db,
                payload=UserCreate(
                    login_name=manager_name, 
                    password=manager_password, 
                    role="manager", 
                    department=manager_dept
                )
            )
            print(f"✅ Başarılı: Manager kullanıcısı sisteme mühürlendi -> {manager_name} ({manager_dept})")
        else:
            print("ℹ️ Manager kullanıcısı veritabanında zaten mevcut, atlanıyor.")

if __name__ == "__main__":
    asyncio.run(seed())