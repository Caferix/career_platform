from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.core.security import require_admin, hash_data # Rol kontrol dependency'si
from app.models.user_model import User  # User modeli (Source 9'daki yapı)
from app.models.company import Department, Position  # Organizasyon modelleri (Source 6)
from app.schemas.admin import DepartmentCreate, DepartmentResponse, PositionCreate, PositionResponse
from app.schemas.user import UserCreate  # Şema klasörünüzdeki mevcut yapı varsayımıyla

router = APIRouter(prefix="/admin", tags=["Admin Operations"], dependencies=[Depends(require_admin)])

# --- DEPARTMAN YÖNETİMİ ---

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(payload: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    """Admin tarafından sisteme dinamik olarak yeni bir departman ekler."""
    stmt = select(Department).where(Department.name == payload.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu departman zaten mevcut.")
    
    new_dept = Department(name=payload.name, is_active=payload.is_active)
    db.add(new_dept)
    await db.commit()
    await db.refresh(new_dept)
    
    #  SQLAlchemy'nin ilişkisel 'positions' alanını tetiklemesini engellemek için 
    # veriyi doğrudan temiz bir Pydantic nesnesine eşleyerek dönüyoruz.
    return DepartmentResponse(
        id=new_dept.id,
        name=new_dept.name,
        is_active=new_dept.is_active,
        positions=[]  # Yeni açılan departmanın henüz hiçbir pozisyonu olmadığı için boş dizi veriyoruz
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
async def create_position(payload: PositionCreate, db: AsyncSession = Depends(get_db)):
    """Belirli bir departmana bağlı dinamik yeni bir iş pozisyonu açar."""
    # Departman kontrolü
    dept_stmt = select(Department).where(Department.id == payload.department_id)
    dept_result = await db.execute(dept_stmt)
    if not dept_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İlgili departman bulunamadı.")

    new_pos = Position(
        name=payload.name,
        department_id=payload.department_id,
        is_active=payload.is_active
    )
    db.add(new_pos)
    await db.commit()
    await db.refresh(new_pos)
    return new_pos

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_system_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Admin tarafından sisteme yeni İK (hr) veya Departman Müdürü (manager) ekler.
    Kullanıcı adı benzersiz olmalıdır. Şifre arka planda hashlenerek saklanır.
    """
    # 1. Kullanıcı adı benzersizlik kontrolü (Kural 4: select)
    stmt = select(User).where(User.login_name == payload.login_name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Bu kullanıcı adı zaten alınmış."
        )
    
    # 2. İş kuralları doğrulaması (Manager için departman şartı)
    if payload.role == "manager" and not payload.department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Departman Müdürü rolü için departman seçimi zorunludur."
        )
        
    if payload.role == "hr":
        payload.department = None  # HR için departman bağımsızdır

    # 3. Şifreyi hashleme ve veritabanına mühürleme
    # Not: Servis katmanınız (user_service.create_user) zaten bu hashlemeyi yapıyorsa 
    # doğrudan servisi de çağırabilirsiniz. Rota seviyesinde manuel ekleyeceksek:
    hashed_pwd = hash_data(payload.password) # Projedeki sync hash motorunuz
    
    new_user = User(
        login_name=payload.login_name,
        hashed_password=hashed_pwd,
        role=payload.role,
        department=payload.department,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "message": f"Kullanıcı başarıyla oluşturuldu: {new_user.login_name}",
        "role": new_user.role
    }