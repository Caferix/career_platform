import os
from fastapi import APIRouter, Depends, UploadFile, File, status, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db  
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate
from app.services import application as app_service
from app.services import storage
from fastapi.responses import FileResponse
from app.models.candidate import Application

# Faz 6 Yetkilendirme ve KVKK Log Servis bağımlılıkları
from app.core.security import require_hr_or_manager
from app.services.access_log import log_access

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_application(
    payload: ApplicationCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Adayın pozisyona ilk başvurusunu kaydeder.
    Mükerrer başvuru kontrolü servis katmanında işletilir.
    """
    return await app_service.create_application(db=db, payload=payload)


@router.post("/{app_id}/upload-cv", response_model=ApplicationResponse)
async def upload_application_cv(
    app_id: int, 
    file: UploadFile = File(..., description="Yüklenecek CV dökümanı (PDF, DOC, DOCX)"), 
    db: AsyncSession = Depends(get_db)
):
    """
    Oluşturulan başvuruya güvenli bir şekilde CV dökümanı yükler.
    Dosya boyutu ve uzantı denetimi arka planda storage servisiyle ortak yürütülür.
    """
    return await app_service.upload_cv_to_application(db=db, app_id=app_id, file=file)


@router.get("/{app_id}/cv")
async def download_cv(
    app_id: int, 
    request: Request,  # IP yakalamak için FastAPI'nin saf istek nesnesi
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager)  # <-- Asenkron Koruma Katmanı
):
    # Başvuruyu getir
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.is_deleted == False
        )
    )
    application = result.scalar_one_or_none()

    if not application or not application.cv_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İstenen döküman bulunamadı.")

    # [ROL FİLTRESİ] Manager ise ve kendi departmanı değilse erişimi engelle
    if current_user.get("role") == "manager" and application.department != current_user.get("department"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )

    file_path = storage.get_file_path(application.cv_url)

    # Güvenlik Kuralı: Dışarıya iç sunucu dosya detaylarını sızdırma
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İstenen döküman sistemde mevcut değil.")

    #  [KVKK DENETİM İZİ] İşlem tamamen doğrulanıp bittiği an mühürleniyor
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
    department: str = Query(None, description="Departmana göre filtreleme"), 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager)  # <-- Asenkron Koruma Katmanı
):
    """İK Yetkilileri için aktif (silinmemiş) tüm başvuruları listeler."""
    
    # [ROL FİLTRESİ] Manager ise sadece kendi departman verisini görebilir, global query ezilir
    if current_user.get("role") == "manager":
        department = current_user.get("department")

    return await app_service.list_applications(db=db, department=department)


@router.patch("/{app_id}/status", response_model=ApplicationResponse)
async def change_application_status(
    app_id: int, 
    payload: ApplicationStatusUpdate, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager)  # <-- Asenkron Koruma Katmanı
):
    """İK Yetkililerinin başvuru statüsünü (pending, under_review vb.) güncellemesini sağlar."""
    
    #  [ROL FİLTRESİ] Manager ise statüsünü değiştireceği başvurunun kendi departmanında olduğunu doğrula
    if current_user.get("role") == "manager":
        result = await db.execute(
            select(Application).where(
                Application.id == app_id,
                Application.is_deleted == False
            )
        )
        application = result.scalar_one_or_none()
        
        if not application or application.department != current_user.get("department"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz bulunmamaktadır."
            )

    updated_record = await app_service.update_application_status(db=db, app_id=app_id, payload=payload)

    # [KVKK DENETİM İZİ] Durum başarıyla değiştirildiğinde log basılıyor
    await log_access(
        db=db,
        user_id=int(current_user["sub"]),
        user_role=current_user["role"],
        action="updated_status",
        target_id=app_id,
        ip_address=request.client.host
    )

    return updated_record