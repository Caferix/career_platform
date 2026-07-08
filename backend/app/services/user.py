from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.models.user_model import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password

async def get_user_by_login_name(db: AsyncSession, login_name: str) -> Optional[User]:
    """Veritabanından kullanıcıyı login_name ile asenkron sorgular."""
    stmt = select(User).where(User.login_name == login_name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    """Yeni bir HR veya Manager kullanıcısını şifresini asenkron hashleyerek kaydeder."""
    hashed = hash_password(payload.password)
    db_user = User(
        login_name=payload.login_name,
        hashed_password=hashed,
        role=payload.role,
        department=payload.department
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, login_name: str, password: str) -> Optional[User]:
    """Kullanıcı giriş bilgilerini asenkron olarak doğrular."""
    user = await get_user_by_login_name(db, login_name)
    if not user or not user.is_active:
        return None
        
    # Asenkron şifre doğrulama motorunu tetikliyoruz
    is_valid = verify_password(password, user.hashed_password)
    if not is_valid:
        return None
        
    return user