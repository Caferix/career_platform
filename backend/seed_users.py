# backend/seed_users.py

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
        # 1. Mevcut .env yapılandırmasını güvenli liman (fallback) olarak koruyoruz
        hr_name     = settings.SEED_HR_LOGIN
        hr_password = settings.SEED_HR_PASSWORD

        if not hr_password:
            hr_password = getattr(settings, "SEED_HR_PASSWORD", None)

        if not hr_password:
            print("❌ HATA: .env dosyasında SEED_HR_PASSWORD okunamadı!")
            return

        # 2. HR Kullanıcısı Kontrol ve Tohumlama (Mevcut kodunuz aynen kalıyor)
        existing_hr = await user_service.get_user_by_login_name(db, hr_name)
        if not existing_hr:
            await user_service.create_user(
                db=db,
                payload=UserCreate(login_name=hr_name, password=hr_password, role="hr")
            )
            print(f"✅ Başarılı: HR kullanıcısı sisteme mühürlendi -> {hr_name}")
        else:
            print("ℹ️ HR kullanıcısı veritabanında zaten mevcut, atlanıyor.")

        # 3. 🌟 YENİ: Fabrika Departman Müdürleri Tohumlama Havuzu
        # company-structure.js dosyasındaki birebir departman isimleriyle eşliyoruz!
        managers_pool = [
            {
                "login_name": "manager_yazilim",
                "password": "ManagerPass123",
                "department": "Yazılım ve AR-GE Mühendisliği"
            },
            {
                "login_name": "manager_uretim",
                "password": "ProductionPass123",
                "department": "Fabrika Üretim ve Montaj Hattı" # Mavi yaka sorumlusu
            },
            {
                "login_name": "manager_lojistik",
                "password": "LogisticsPass123",
                "department": "Satın Alma ve Lojistik"
            },
            {
                "login_name": "manager_bakim",
                "password": "MaintenancePass123",
                "department": "Bakım onarım ve Tesis Yönetimi"
            }
        ]

        # Döngüyle tüm havuzu veritabanına mühürlüyoruz
        for mgr in managers_pool:
            existing_mgr = await user_service.get_user_by_login_name(db, mgr["login_name"])
            if not existing_mgr:
                await user_service.create_user(
                    db=db,
                    payload=UserCreate(
                        login_name=mgr["login_name"], 
                        password=mgr["password"], 
                        role="manager", 
                        department=mgr["department"]
                    )
                )
                print(f"✅ Başarılı: Departman Müdürü mühürlendi -> {mgr['login_name']} [{mgr['department']}]")
            else:
                print(f"ℹ️ {mgr['login_name']} veritabanında zaten mevcut, atlanıyor.")

if __name__ == "__main__":
    asyncio.run(seed())