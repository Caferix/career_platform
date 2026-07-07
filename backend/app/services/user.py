from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_model import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password
from app.core.departments import parse_departments

async def get_user_by_login_name(db: AsyncSession, login_name: str) -> User | None:
    stmt = select(User).where(User.login_name == login_name)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed = hash_password(user_in.password)
    departments = parse_departments(user_in.department)
    db_user = User(
        login_name=user_in.login_name,
        hashed_password=hashed,
        role=user_in.role,
        department=",".join(departments) if departments else None
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, login_name: str, password: str) -> User | None:
    user = await get_user_by_login_name(db, login_name)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user