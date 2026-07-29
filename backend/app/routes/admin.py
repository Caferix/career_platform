from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_loader_criteria
from datetime import datetime, timezone
from app.db.database import get_db
from app.core.security import require_admin, hash_data, get_current_user,require_hr_or_manager # Rol kontrol dependency'si
from app.core.permissions import get_department_filter, can_manage_users, can_delete_candidate
from app.models.user_model import User  # User modeli (Source 9'daki yapı)
from app.models.company import Department, Position  # Organizasyon modelleri (Source 6)
from app.schemas.admin import DepartmentCreate, DepartmentUpdate, DepartmentResponse, PositionCreate, PositionUpdate, PositionResponse
from app.schemas.user import UserCreate  # Şema klasörünüzdeki mevcut yapı varsayımıyla
from app.models.candidate import Candidate
from app.models.consents import AccessLog
from typing import Optional
from app.models.auth_log import FailedLoginAttempt
from app.services.access_log import log_access



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
    stmt = (
        select(Department)
        .where(Department.is_deleted == False)
        .options(
            selectinload(Department.positions),
            with_loader_criteria(Position, Position.is_deleted == False)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/departments/{id}", response_model=DepartmentResponse)
async def update_department(
    id: int,
    payload: DepartmentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not can_manage_users(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmuyor.")

    stmt = select(Department).where(Department.id == id, Department.is_deleted == False)
    result = await db.execute(stmt)
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departman bulunamadı.")
        
    if payload.name is not None:
        department.name = payload.name
    if payload.is_active is not None:
        department.is_active = payload.is_active
        
    await db.commit()
    await db.refresh(department)
    
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action=f"Departman Güncellendi: {department.name}",
        target_id=department.id,
        ip_address=request.client.host
    )
    
    return department

@router.delete("/departments/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Departmanı siler (Soft Delete). Bağlı pozisyonlar ve ilanlar da pasife çekilir/silinir."""
    if not can_manage_users(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmuyor.")

    stmt = select(Department).where(Department.id == id, Department.is_deleted == False)
    result = await db.execute(stmt)
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departman bulunamadı.")
        
    # Soft delete department
    department.is_deleted = True
    department.is_active = False
    
    # Soft cascade on positions
    pos_stmt = select(Position).where(Position.department_id == department.id, Position.is_deleted == False)
    pos_result = await db.execute(pos_stmt)
    positions = pos_result.scalars().all()
    for pos in positions:
        pos.is_deleted = True
        pos.is_active = False
        
    # Import JobPosting here if not imported at top
    from app.models.job_posting import JobPosting
    job_stmt = select(JobPosting).where(JobPosting.department_id == department.id, JobPosting.is_deleted == False)
    job_result = await db.execute(job_stmt)
    jobs = job_result.scalars().all()
    for job in jobs:
        job.is_deleted = True
        job.is_active = False
        job.deleted_at = datetime.utcnow()
        
    await db.commit()
    
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action=f"Departman Askıya Alındı: {department.name}",
        target_id=department.id,
        ip_address=request.client.host
    )
    
    return None

# --- POZİSYON YÖNETİMİ ---

@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    payload: PositionCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Sistem yöneticileri tarafından dinamik olarak yeni bir iş ilanı (pozisyon) ekler."""
    if not can_manage_users(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmuyor.")

    dept_stmt = select(Department).where(Department.id == payload.department_id)
    dept_result = await db.execute(dept_stmt)
    department = dept_result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İlgili departman bulunamadı.")
        
    # title yerine name ile kontrol ediyoruz
    pos_stmt = select(Position).where(
        Position.name == payload.name, 
        Position.department_id == payload.department_id
    )
    pos_result = await db.execute(pos_stmt)
    if pos_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu departman altında bu pozisyon zaten mevcut.")

    # description'ı çıkardık, title yerine name kullandık
    new_position = Position(
        name=payload.name,
        is_active=payload.is_active,
        department_id=payload.department_id
    )
    db.add(new_position)
    await db.commit()
    await db.refresh(new_position)
    
    return new_position

@router.patch("/positions/{id}", response_model=PositionResponse)
async def update_position(
    id: int,
    payload: PositionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not can_manage_users(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmuyor.")

    stmt = select(Position).where(Position.id == id, Position.is_deleted == False)
    result = await db.execute(stmt)
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pozisyon bulunamadı.")
        
    if payload.name is not None:
        position.name = payload.name
    if payload.is_active is not None:
        position.is_active = payload.is_active
    if payload.department_id is not None:
        # Check if new department exists
        dept_stmt = select(Department).where(Department.id == payload.department_id, Department.is_deleted == False)
        dept_res = await db.execute(dept_stmt)
        if not dept_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Belirtilen departman bulunamadı.")
        position.department_id = payload.department_id
        
    await db.commit()
    await db.refresh(position)
    
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action=f"Pozisyon Güncellendi: {position.name}",
        target_id=position.id,
        ip_address=request.client.host
    )
    
    return position

@router.delete("/positions/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pozisyonu siler (Soft Delete). Bağlı ilanlar da pasife çekilir/silinir."""
    if not can_manage_users(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmuyor.")

    stmt = select(Position).where(Position.id == id, Position.is_deleted == False)
    result = await db.execute(stmt)
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pozisyon bulunamadı.")
        
    # Soft delete position
    position.is_deleted = True
    position.is_active = False
    
    # Soft cascade on job postings
    from app.models.job_posting import JobPosting
    job_stmt = select(JobPosting).where(JobPosting.position_id == position.id, JobPosting.is_deleted == False)
    job_result = await db.execute(job_stmt)
    jobs = job_result.scalars().all()
    for job in jobs:
        job.is_deleted = True
        job.is_active = False
        job.deleted_at = datetime.utcnow()
        
    await db.commit()
    
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action=f"Pozisyon Askıya Alındı: {position.name}",
        target_id=position.id,
        ip_address=request.client.host
    )
    
    return None

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
        hashed_password=hashed_pwd,
        role=payload.role,
        department=payload.department
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    request = Depends(Request)
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action="created_system_user",
        target_id=new_user.id,
        ip_address="127.0.0.1"
    )
    
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

    # Her sorguda is_deleted=False süzgeci işletilir (Aktif adayı bul)
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

    # KVKK Audit Log
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action="archived_candidate",
        target_id=id,
        ip_address="127.0.0.1"
    )

    return {
        "status": "Success",
        "message": f"{id} ID'li aday başarıyla arşivlendi (soft-deleted)."
    }


@router.get("/access-logs", status_code=status.HTTP_200_OK)
async def get_access_logs(
    user_role: Optional[str] = Query(None, description="Kullanıcı rolüne göre filtrele"),
    action: Optional[str] = Query(None, description="Yapılan aksiyona göre filtrele (Örn: downloaded_cv)"),
    date_from: Optional[datetime] = Query(None, description="Bu tarihten itibaren (YYYY-MM-DD HH:MM:SS)"),
    date_to: Optional[datetime] = Query(None, description="Bu tarihe kadar (YYYY-MM-DD HH:MM:SS)"),
    limit: int = Query(50, ge=1, le=100, description="Sayfa başına getirilecek kayıt sayısı"),
    offset: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Sistem yöneticilerinin hareketlerini takip edebilecek sorgu altyapısı.
    Sadece süperadmin rütbesine açık asenkron filtreleme ve sayfalama altyapısı sunar.
    """
    # Güvenlik Kontrolü: Yalnızca can_manage_users izni olan (Superadmin) erişebilir
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu log verilerine erişim yetkiniz bulunmuyor."
        )

    # Temel sorgu oluşturma (En son log en üstte görünecek şekilde sıralı)
    stmt = select(AccessLog).order_by(AccessLog.id.desc())

    # Dinamik Filtreleme Kuralları
    if user_role:
        stmt = stmt.where(AccessLog.user_role == user_role)
    if action:
        stmt = stmt.where(AccessLog.action == action)
    if date_from:
        stmt = stmt.where(AccessLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AccessLog.created_at <= date_to)

    # Sayfalama (Pagination)
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "limit": limit,
        "offset": offset,
        "results": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_role": log.user_role,
                "action": log.action,
                "target_id": log.target_id,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }


# --- FAZ 4: BAŞARISIZ GİRİŞLER ENDPOINT (Adım 4.2) ---

@router.get("/failed-logins", status_code=status.HTTP_200_OK)
async def get_failed_logins(
    login_name: Optional[str] = Query(None, description="Hatalı deneme yapılan kullanıcı adına göre filtrele"),
    ip_address: Optional[str] = Query(None, description="Şüpheli IP adresine göre filtrele"),
    limit: int = Query(50, ge=1, le=100, description="Getirilecek maksimum kayıt sayısı"),
    offset: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Son kaba kuvvet (brute-force) denemelerinin ve şüpheli IP adreslerinin
    süperadmin ekranında asenkron olarak listelenmesini sağlar.
    """
    # Güvenlik Kontrolü: Yalnızca can_manage_users izni olan (Superadmin) erişebilir
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu verileri görüntüleme yetkiniz bulunmuyor."
        )

    # En son yapılan hatalı deneme en üstte görünecek şekilde sorgu kurulur
    stmt = select(FailedLoginAttempt).order_by(FailedLoginAttempt.id.desc())

    # Filtrelerin Uygulanması
    if login_name:
        stmt = stmt.where(FailedLoginAttempt.login_name == login_name)
    if ip_address:
        stmt = stmt.where(FailedLoginAttempt.ip_address == ip_address)

    # Sayfalama
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    attempts = result.scalars().all()

    return {
        "limit": limit,
        "offset": offset,
        "results": [
            {
                "id": attempt.id,
                "login_name": attempt.login_name,
                "ip_address": attempt.ip_address,
                "attempted_at": attempt.attempted_at
            }
            for attempt in attempts
        ]
    }


@router.get("/users", status_code=status.HTTP_200_OK)
async def list_system_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Sistemdeki tüm yöneticileri (HR, Manager vb.) listeler."""
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bu işlem için yetkiniz bulunmuyor."
        )

    # Veritabanındaki tüm kurumsal kullanıcıları çekiyoruz
    stmt = select(User).order_by(User.id.asc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    # Ön yüzün (admin.html) fetchUsers() fonksiyonunun beklediği JSON formatında dönüyoruz
    return [
        {
            "id": user.id,
            "login_name": user.login_name,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active if hasattr(user, 'is_active') else True
        }
        for user in users
    ]


@router.post("/users/{user_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_user_status(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """İlgili sistem kullanıcısının aktiflik durumunu tersine çevirir."""
    if not can_manage_users(current_user):
        raise HTTPException(status_code=403, detail="Yetkiniz yok.")
        
    # ENGEL 1: Kullanıcı KENDİ hesabını pasife alamaz!
    if int(current_user["sub"]) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Kendi hesabınızın aktiflik durumunu değiştiremezsiniz!"
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    # ENGEL 2: 'admin' veya 'superadmin' rolündeki hesaplar pasife alınamaz!
    if user.role in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Yönetici (Admin/Superadmin) hesapları pasif duruma getirilemez."
        )
        
    if hasattr(user, 'is_active'):
        user.is_active = not user.is_active
        await db.commit()

        await log_access(
            db=db,
            user_id=int(current_user["sub"]),
            user_role=current_user.get("role"),
            action=f"Kullanıcı Durumu Değiştirildi: {user.login_name}",
            target_id=user.id,
            ip_address=request.client.host
        )
        
    return {"status": "success", "message": "Kullanıcı durumu güncellendi."}

@router.delete("/departments/{dept_id}", status_code=status.HTTP_200_OK)
async def deactivate_department(
    dept_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Departmanı ve bağlı tüm pozisyonları pasife alır (Veri bütünlüğü için soft delete)."""
    if not can_manage_users(current_user):
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok.")

    stmt = select(Department).options(selectinload(Department.positions)).where(Department.id == dept_id)
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()

    if not dept:
        raise HTTPException(status_code=404, detail="Departman bulunamadı.")

    dept.is_active = False
    for pos in dept.positions:
        pos.is_active = False

    await db.commit()
    return {"message": "Departman ve bağlı pozisyonlar başarıyla pasife alındı."}


@router.delete("/positions/{pos_id}", status_code=status.HTTP_200_OK)
async def deactivate_position(
    pos_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pozisyonu pasife alır."""
    if not can_manage_users(current_user):
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok.")

    stmt = select(Position).where(Position.id == pos_id)
    result = await db.execute(stmt)
    pos = result.scalar_one_or_none()

    if not pos:
        raise HTTPException(status_code=404, detail="Pozisyon bulunamadı.")

    pos.is_active = False
    await db.commit()
    return {"message": "Pozisyon başarıyla pasife alındı."}