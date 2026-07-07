import os
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db  
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate
from app.services import application as app_service
from app.services.access_log import log_access
from app.services import storage
from fastapi.responses import FileResponse
from app.models.candidate import Application
from app.core.security import require_hr, require_hr_or_manager
from app.core.departments import authorized_departments, normalize_department

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_application(
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
    application = await app_service.get_application_by_id(db, app_id)

    if not application or not application.cv_url:
        raise HTTPException(status_code=404, detail="CV bulunamadı.")

    if current_user.get("role") == "manager" and normalize_department(application.department) not in authorized_departments(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmamaktadır.")

    file_path = storage.get_file_path(application.cv_url)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dosya sistemde bulunamadı.")

    await log_access(
        db=db,
        user_id=current_user.get("user_id", 0),
        user_role=current_user.get("role", ""),
        action="downloaded_cv",
        target_id=app_id,
        ip_address=request.client.host if request.client else None,
    )

    return FileResponse(
        path=file_path,
        filename=f"cv_{app_id}.pdf",
        media_type="application/octet-stream"
    )


@router.get("/", response_model=list[ApplicationResponse])
async def get_all_applications(
    department: str = Query(None, description="Departmana göre filtreleme"), 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager)
):
    """İK Yetkilileri için aktif (silinmemiş) tüm başvuruları listeler."""
    effective_departments = [department] if department else None
    if current_user.get("role") == "manager":
        effective_departments = authorized_departments(current_user)

    return await app_service.list_applications(db=db, departments=effective_departments)


@router.patch("/{app_id}/status", response_model=ApplicationResponse)
async def change_application_status(
    app_id: int, 
    payload: ApplicationStatusUpdate, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager)
):
    """İK Yetkililerinin başvuru statüsünü güncellemesini sağlar."""
    application = await app_service.get_application_by_id(db, app_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Başvuru bulunamadı.")

    if current_user.get("role") == "manager" and normalize_department(application.department) not in authorized_departments(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yetkiniz bulunmamaktadır.")

    updated_application = await app_service.update_application_status(db=db, app_id=app_id, payload=payload)

    await log_access(
        db=db,
        user_id=current_user.get("user_id", 0),
        user_role=current_user.get("role", ""),
        action="updated_status",
        target_id=app_id,
        ip_address=request.client.host if request.client else None,
    )

    return updated_application