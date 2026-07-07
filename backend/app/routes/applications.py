import os
from fastapi import APIRouter, Depends, UploadFile, File, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db  # Projendeki DB session dependency'si
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate
from app.services import application as app_service
from app.services import storage
from fastapi.responses import FileResponse
from app.models.candidate import Application




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
async def download_cv(app_id: int, db: AsyncSession = Depends(get_db)):
    # Başvuruyu getir
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.is_deleted == False
        )
    )
    application = result.scalar_one_or_none()

    if not application or not application.cv_url:
        raise HTTPException(status_code=404, detail="CV bulunamadı.")

    file_path = storage.get_file_path(application.cv_url)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dosya sistemde bulunamadı.")

    return FileResponse(
        path=file_path,
        filename=f"cv_{app_id}.pdf",
        media_type="application/octet-stream"
    )


@router.get("/", response_model=list[ApplicationResponse])
async def get_all_applications(
    department: str = Query(None, description="Departmana göre filtreleme"), 
    db: AsyncSession = Depends(get_db)
):
    """İK Yetkilileri için aktif (silinmemiş) tüm başvuruları listeler."""
    return await app_service.list_applications(db=db, department=department)


@router.patch("/{app_id}/status", response_model=ApplicationResponse)
async def change_application_status(
    app_id: int, 
    payload: ApplicationStatusUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """İK Yetkililerinin başvuru statüsünü (pending, under_review vb.) güncellemesini sağlar."""
    return await app_service.update_application_status(db=db, app_id=app_id, payload=payload)