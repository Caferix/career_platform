from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from app.db.database import get_db
from app.core.security import require_admin, hash_data, get_current_user,require_hr_or_manager # Rol kontrol dependency'si
from app.core.permissions import get_department_filter, can_manage_users, can_delete_candidate
from app.models.user_model import User  # User modeli (Source 9'daki yapı)
from app.models.company import Department, Position  # Organizasyon modelleri (Source 6)
from app.schemas.admin import DepartmentCreate, DepartmentResponse, PositionCreate, PositionResponse
from app.schemas.user import UserCreate  # Şema klasörünüzdeki mevcut yapı varsayımıyla
from app.models.candidate import Candidate

router = APIRouter(prefix="/admin", tags=["Admin Operations"], dependencies=[Depends(require_admin)])

# --- DEPARTMAN YÖNETİMİ ---

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Admin/Superadmin tarafından sisteme dinamik olarak yeni bir departman ekler."""
    # Katı rol kontrolü yerine yetki soyutlama matrisini tetikliyoruz
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bu işlem için yetkiniz bulunmuyor."
        )

    stmt = select(Department).where(Department.name == payload.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu departman zaten mevcut.")
    
    new_dept = Department(name=payload.name, is_active=payload.is_active)
    db.add(new_dept)
    await db.commit()
    await db.refresh(new_dept)
    
    return DepartmentResponse(
        id=new_dept.id,
        name=new_dept.name,
        is_active=new_dept.is_active,
        positions=[]
    )


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db)):
    """Sistemdeki tüm departmanları bağlı pozisyonları ile asenkron getirir."""
    # Kural 4: selectinload ile ilişkisel veriyi asenkron çekme
    stmt = select(Department).options(selectinload(Department.positions))
    result = await db.execute(stmt)
    return result.scalars().all()

# --- POZİSYON YÖNETİMİ ---

@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    payload: PositionCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Sistem yöneticileri tarafından dinamik olarak yeni bir iş ilanı (pozisyon) ekler."""
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bu işlem için yetkiniz bulunmuyor."
        )

    dept_stmt = select(Department).where(Department.id == payload.department_id)
    dept_result = await db.execute(dept_stmt)
    department = dept_result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İlgili departman bulunamadı.")
        
    pos_stmt = select(Position).where(
        Position.title == payload.title, 
        Position.department_id == payload.department_id
    )
    pos_result = await db.execute(pos_stmt)
    if pos_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu departman altında bu pozisyon zaten mevcut.")

    new_position = Position(
        title=payload.title,
        description=payload.description,
        is_active=payload.is_active,
        department_id=payload.department_id
    )
    db.add(new_position)
    await db.commit()
    await db.refresh(new_position)
    
    return PositionResponse(
        id=new_position.id,
        title=new_position.title,
        description=new_position.description,
        is_active=new_position.is_active,
        department_id=new_position.department_id
    )

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_system_user(
    payload: UserCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Sisteme yeni İK (hr) veya Departman Müdürü (manager) ekler."""
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bu işlem için yetkiniz bulunmuyor."
        )

    stmt = select(User).where(User.login_name == payload.login_name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış.")
    
    hashed_pwd = hash_data(payload.password)
    new_user = User(
        login_name=payload.login_name,
        password_hash=hashed_pwd,
        role=payload.role,
        department=payload.department
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "login_name": new_user.login_name,
        "role": new_user.role,
        "department": new_user.department
    }

@router.delete("/candidates/{id}", status_code=status.HTTP_200_OK)
async def soft_delete_candidate(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Adayların sistemden soft-delete işlem yetkisini sadece süperadmin rütbesine çeker.
    Kayıt fiziksel olarak silinmez, is_deleted bayrağı ve silinme zamanı işaretlenir.
    """
    # Yetki soyutlama katmanından sadece superadmin geçişine izin veriyoruz
    if not can_delete_candidate(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmuyor. Aday silme yetkisi sadece Süperadmin rütbesine aittir."
        )

    # Kural 11: Her sorguda is_deleted=False süzgeci işletilir (Aktif adayı bul)
    stmt = select(Candidate).where(Candidate.id == id, Candidate.is_deleted == False)
    result = await db.execute(stmt)
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belirtilen aday bulunamadı veya zaten silinmiş."
        )

    # Fiziksel silme yerine soft-delete uyguluyoruz
    candidate.is_deleted = True
    candidate.deleted_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "status": "Success",
        "message": f"{id} ID'li aday başarıyla arşivlendi (soft-deleted)."
    }