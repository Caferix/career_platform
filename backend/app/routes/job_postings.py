from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from app.db.database import get_db
from app.core.security import get_current_user, require_hr_or_manager
from app.models.job_posting import JobPosting
from app.models.company import Position, Department
from app.schemas.job_posting import JobPostingCreate, JobPostingUpdate, JobPostingResponse
from app.services.access_log import log_access

router = APIRouter(
    prefix="/jobs", 
    tags=["Job Posting Operations"], 
    dependencies=[Depends(require_hr_or_manager)]
)

# 1. YENİ İLAN OLUŞTURMA (POST)
@router.post("", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job_posting(
    payload: JobPostingCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Yeni ilan oluşturur. 
    Manager'lar sadece kendi bağlı olduğu departmana ait pozisyonlar için ilan açabilir.
    """
    user_role = current_user.get("role")
    user_dept_name = current_user.get("department")

    # Pozisyonun varlığını ve bağlı olduğu departmanı doğruluyoruz
    pos_stmt = select(Position).options(selectinload(Position.department)).where(Position.id == payload.position_id)
    pos_result = await db.execute(pos_stmt)
    position = pos_result.scalar_one_or_none()

    if not position:
        raise HTTPException(status_code=404, detail="Seçilen pozisyon sistemde bulunamadı.")

    # Manager Kısıtlaması: Manager kendi departmanı dışındaki pozisyona ilan açamaz
    if user_role == "manager" and position.department.name != user_dept_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Sadece kendi departmanınız ({user_dept_name}) adına ilan açabilirsiniz."
        )

    new_job = JobPosting(
        department_id=position.department_id,
        position_id=position.id,
        created_by_user_id=int(current_user["sub"]),
        title=payload.title,
        description=payload.description,
        location=payload.location,
        expires_at=payload.expires_at,
        is_active=True
    )

    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # Access Log Kaydı
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=user_role,
        action="created_job_posting",
        target_id=new_job.id,
        ip_address=request.client.host
    )

    return new_job


# 2. İLANLARI LİSTELEME (GET)
@router.get("", response_model=list[JobPostingResponse])
async def list_department_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    HR ve Admin tüm ilanları görür.
    Manager sadece kendi departmanına ait açılan ilanları görür.
    """
    user_role = current_user.get("role")
    user_dept_name = current_user.get("department")

    stmt = select(JobPosting).where(JobPosting.is_deleted == False)

    if user_role == "manager":
        # Manager için departman id'sini çekip filtreliyoruz
        dept_stmt = select(Department).where(Department.name == user_dept_name)
        dept_result = await db.execute(dept_stmt)
        dept = dept_result.scalar_one_or_none()

        if not dept:
            return []
        
        stmt = stmt.where(JobPosting.department_id == dept.id)

    stmt = stmt.order_by(JobPosting.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# 3. İLAN DÜZENLEME / GÜNCELLEME (PUT/PATCH) -> İSTEDİĞİN DÜZENLEME ADIMI
@router.patch("/{job_id}", response_model=JobPostingResponse)
async def update_job_posting(
    job_id: int,
    payload: JobPostingUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Açılmış ilanın başlığını, açıklamasını, lokasyonunu veya son başvuru tarihini günceller.
    Manager sadece kendi departmanındaki ilanı düzenleyebilir.
    """
    stmt = select(JobPosting).where(JobPosting.id == job_id, JobPosting.is_deleted == False)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")

    # Manager Yetki Kontrolü
    user_role = current_user.get("role")
    user_dept_name = current_user.get("department")

    if user_role == "manager":
        dept_stmt = select(Department).where(Department.id == job.department_id)
        dept_res = await db.execute(dept_stmt)
        job_dept = dept_res.scalar_one_or_none()

        if not job_dept or job_dept.name != user_dept_name:
            raise HTTPException(status_code=403, detail="Başka departmanın ilanını düzenleyemezsiniz.")

    # Sadece gönderilen alanları dinamik güncelliyoruz
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job, key, value)

    await db.commit()
    await db.refresh(job)

    # Log
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=user_role,
        action="updated_job_posting",
        target_id=job.id,
        ip_address=request.client.host
    )

    return job


# 4. İLAN DURUMU TERSİNE ÇEVİRME / YAYINDAN KALDIRMA (POST Toggle)
@router.post("/{job_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_job_status(
    job_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    İlanın aktiflik durumunu tersine çevirir (Aktifse Pasife, Pasifse Aktife alır).
    """
    stmt = select(JobPosting).where(JobPosting.id == job_id, JobPosting.is_deleted == False)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")

    job.is_active = not job.is_active
    await db.commit()

    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action="toggled_job_status",
        target_id=job.id,
        ip_address=request.client.host
    )

    return {
        "status": "success",
        "is_active": job.is_active,
        "message": f"İlan durumu {'Aktif' if job.is_active else 'Pasif'} olarak değiştirildi."
    }