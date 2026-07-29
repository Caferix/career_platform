import os
from fastapi import APIRouter, Depends, UploadFile, File, status, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import FileResponse

from app.db.database import get_db  
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate
from app.services import application as app_service
from app.services import storage
from app.models.candidate import Application

# Yeni Yetki Katmanı import edildi
from app.core.permissions import get_department_filter
from app.core.security import require_hr_or_manager, get_current_user
from app.services.access_log import log_access
from app.core.security import require_hr_or_manager, limiter

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def create_new_application(
    request: Request,
    payload: ApplicationCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Adayın pozisyona ilk başvurusunu kaydeder."""
    return await app_service.create_application(db=db, payload=payload)


@router.post("/{app_id}/upload-cv", response_model=ApplicationResponse)
async def upload_application_cv(
    app_id: int, 
    file: UploadFile = File(..., description="Yüklenecek CV dökümanı (PDF, DOC, DOCX)"), 
    db: AsyncSession = Depends(get_db)
):
    """Oluşturulan başvuruya güvenli bir şekilde CV dökümanı yükler."""
    return await app_service.upload_cv_to_application(db=db, app_id=app_id, file=file)


@router.get("/{app_id}/cv")
async def download_cv(
    app_id: int, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager)
):
    #  Soyutlanmış departman filtresini alıyoruz
    dept_filter = get_department_filter(current_user)
    if dept_filter is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmamaktadır.")

    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.is_deleted == False
        )
    )
    application = result.scalar_one_or_none()

    if not application or not application.cv_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İstenen döküman bulunamadı.")

    #  Koda gömülü rol yerine filtre değerini check ediyoruz (Eğer kısıt varsa ve departman uymuyorsa)
    if dept_filter and application.department != dept_filter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )

    file_path = storage.get_file_path(application.cv_url)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İstenen döküman sistemde mevcut değil.")

    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user["role"],
        action="downloaded_cv",
        target_id=app_id,
        ip_address=request.client.host
    )

    return FileResponse(
        path=file_path,
        filename=f"cv_{app_id}.pdf",
        media_type="application/octet-stream"
    )


@router.get("/", response_model=list[ApplicationResponse])
async def get_all_applications(
    request: Request,
    department: str = Query(None, description="Departmana göre filtreleme"), 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # <-- require_hr_or_manager yerine get_current_user yapıldı
):
    """Aktif başvuruları yetki sınırlarına göre listeler. Admin/Superadmin her şeyi, Manager sadece kendi alanını görür."""
    
    user_role = current_user.get("role")

    # 1. Admin ise hiçbir süzgece takılmadan direkt geçsin
    if user_role in ["admin"]:
        return await app_service.list_applications(db=db, department=department)

    # 2. Eğer admin değilse (HR veya Manager ise) departman filtresini tetikle
    dept_filter = get_department_filter(current_user)
    if dept_filter is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmamaktadır.")

    # Eğer filtre kısıtlıysa (Manager durumu), dışarıdan gelen query ezilir ve kendi departmanı basılır
    if dept_filter:
        department = dept_filter

    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user.get("role"),
        action="viewed_applications_list",
        target_id=None,
        ip_address=request.client.host
    )    

    return await app_service.list_applications(db=db, department=department)


@router.patch("/{app_id}/status", response_model=ApplicationResponse)
async def change_application_status(
    app_id: int, 
    payload: ApplicationStatusUpdate, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager)
):
    """Başvuru statüsünü yetki dahilinde günceller."""
    dept_filter = get_department_filter(current_user)
    if dept_filter is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmamaktadır.")

    # Yetki kısıtlaması kontrolü
    if dept_filter:
        result = await db.execute(
            select(Application).where(
                Application.id == app_id,
                Application.is_deleted == False
            )
        )
        application = result.scalar_one_or_none()
        
        if not application or application.department != dept_filter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz bulunmamaktadır."
            )

    updated_record = await app_service.update_application_status(db=db, app_id=app_id, payload=payload)

    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user["role"],
        action="updated_status",
        target_id=app_id,
        ip_address=request.client.host
    )

    return updated_record

@router.patch("/{app_id}/withdraw", status_code=status.HTTP_200_OK)
async def withdraw_application(
    app_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Adayın başvurusunu iptal etmesini (Geri Çekmesini) sağlar."""
    if current_user.get("role") != "applicant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sadece adaylar başvuru iptali yapabilir.")

    candidate_id = int(current_user.get("user_id"))
    
    stmt = select(Application).where(Application.id == app_id, Application.applicant_id == candidate_id, Application.is_deleted == False)
    result = await db.execute(stmt)
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Başvuru bulunamadı.")
        
    # İş kuralı: "applied" dışındakiler iptal edilemez (veya pending vb)
    # Varsayılan başlangıç durumu "pending" veya "applied" ise izin ver.
    valid_withdraw_statuses = ["pending", "applied", "taslak", "draft"]
    if application.status.lower() not in valid_withdraw_statuses:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bu başvuru değerlendirme aşamasına geçtiği için geri çekilemez."
        )
        
    # Başvuruyu geri çekme mantığı:
    application.is_deleted = True
    application.status = "withdrawn"
    application.deleted_at = __import__('datetime').datetime.utcnow()
    
    await db.commit()
    
    await log_access(
        db=db,
        user_id=candidate_id,
        user_role="candidate",
        action="withdrew_application",
        target_id=application.id,
        ip_address=request.client.host
    )
    
    return {"message": "Başvurunuz başarıyla geri çekilmiştir."}

