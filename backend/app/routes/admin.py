from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.core.security import require_admin  # Rol kontrol dependency'si
from app.models.user_model import User  # User modeli (Source 9'daki yapı)
from app.models.organization import Department, Position  # Organizasyon modelleri (Source 6)
from app.schemas.admin import DepartmentCreate, DepartmentResponse, PositionCreate, PositionResponse
from app.schemas.user import UserCreate  # Şema klasörünüzdeki mevcut yapı varsayımıyla

router = APIRouter(prefix="/admin", tags=["Admin Operations"], dependencies=[Depends(require_admin)])

# --- DEPARTMAN YÖNETİMİ ---

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(payload: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    """Admin tarafından sisteme dinamik olarak yeni bir departman ekler."""
    # Kural 4: select() kullanımı
    stmt = select(Department).where(Department.name == payload.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu departman zaten mevcut.")
    
    new_dept = Department(name=payload.name, is_active=payload.is_active)
    db.add(new_dept)
    await db.commit()
    await db.refresh(new_dept)
    return new_dept

@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db)):
    """Sistemdeki tüm departmanları bağlı pozisyonları ile asenkron getirir."""
    # Kural 4: selectinload ile ilişkisel veriyi asenkron çekme
    stmt = select(Department).options(selectinload(Department.positions))
    result = await db.execute(stmt)
    return result.scalars().all()

# --- POZİSYON YÖNETİMİ ---

@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(payload: PositionCreate, db: AsyncSession = Depends(get_db)):
    """Belirli bir departmana bağlı dinamik yeni bir iş pozisyonu açar."""
    # Departman kontrolü
    dept_stmt = select(Department).where(Department.id == payload.department_id)
    dept_result = await db.execute(dept_stmt)
    if not dept_result.scalar_one_or_none():
        raise HTTPException(status_code=44, detail="İlgili departman bulunamadı.")

    new_pos = Position(
        name=payload.name,
        department_id=payload.department_id,
        is_active=payload.is_active
    )
    db.add(new_pos)
    await db.commit()
    await db.refresh(new_pos)
    return new_pos