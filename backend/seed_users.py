import asyncio
import os
from sys import path

path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.schemas.user import UserCreate
from app.services.user import get_user_by_login_name, create_user
from app.core.departments import parse_departments
from dotenv import load_dotenv

load_dotenv()


async def seed():
    # .env içerisinden kurumsal sırlar ve departman okunuyor
    hr_login = os.getenv("HR_LOGIN_NAME")
    hr_password = os.getenv("HR_PASSWORD")
    manager_login = os.getenv("MANAGER_LOGIN_NAME")
    manager_password = os.getenv("MANAGER_PASSWORD")
    manager_departments = os.getenv("MANAGER_DEPARTMENTS") or os.getenv("MANAGER_DEPARTMENT", "embedded")

    if not all([hr_login, hr_password, manager_login, manager_password]):
        print("[SEED ERROR] Lütfen .env dosyasındaki LOGIN_NAME ve PASSWORD alanlarını doldurun!")
        return

    async with SessionLocal() as db:
        # 1. HR Kullanıcısı Oluşturma
        hr_exists = await get_user_by_login_name(db, hr_login)
        if not hr_exists:
            hr_user = UserCreate(
                login_name=hr_login,
                password=hr_password,
                role="hr"
            )
            await create_user(db, hr_user)
            print(f"[SEED] HR kullanıcısı başarıyla oluşturuldu: {hr_login}")
        
        # 2. Manager Kullanıcısı Oluşturma
        manager_exists = await get_user_by_login_name(db, manager_login)
        if not manager_exists:
            manager_user = UserCreate(
                login_name=manager_login,
                password=manager_password,
                role="manager",
                department=",".join(parse_departments(manager_departments)) or "embedded"
            )
            await create_user(db, manager_user)
            print(f"[SEED] Manager kullanıcısı başarıyla oluşturuldu: {manager_login} ({manager_departments})")


if __name__ == "__main__":
    asyncio.run(seed())