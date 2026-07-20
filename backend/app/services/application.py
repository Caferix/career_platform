import logging
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.candidate import Application
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate
from app.services import storage

logger = logging.getLogger(__name__)

async def create_application(db: AsyncSession, payload: ApplicationCreate) -> Application:
    """Mükerrer başvuru kontrolü yaparak yeni bir başvuru kaydı oluşturur."""
    
    # İş Kuralı: Bir aday aynı pozisyona aktif (silinmemiş) tek bir başvuru yapabilir.
    query = select(Application).where(
        and_(
            Application.applicant_id == payload.applicant_id,
            Application.position == payload.position,
            Application.is_deleted == False
        )
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu pozisyon için halihazırda aktif bir başvurunuz bulunmaktadır."
        )
        
    # Yeni model alanlarına göre güncellenmiş kayıt
    new_app = Application(
        applicant_id=payload.applicant_id,
        position=payload.position,
        department=payload.department,
        experience_years=payload.experience_years,
        experience_detail=payload.experience_detail,
        cover_letter=payload.cover_letter,
        reference_name=payload.reference_name,
        reference_position=payload.reference_position,
        reference_contact=payload.reference_contact, # Property setter ile otomatik şifrelenir
        status="Applied"
    )
    db.add(new_app)
    await db.commit()
    await db.refresh(new_app)
    return new_app

async def upload_cv_to_application(db: AsyncSession, app_id: int, file: UploadFile) -> Application:
    """Başvuru kaydına güvenli bir şekilde CV atar, varsa eskisini diskten temizler."""
    query = select(Application).where(and_(Application.id == app_id, Application.is_deleted == False))
    result = await db.execute(query)
    app_record = result.scalar_one_or_none()
    
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Başvuru kaydı bulunamadı.")
        
    if app_record.cv_url:
        storage.delete_file(app_record.cv_url)
        
    try:
        saved_filename = await storage.save_file(file)
    except ValueError as ve:
        # storage servisinden gelen hata mesajını jenerik hale getirmek istersen burayı da maskeleyebilirsin
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        
    app_record.cv_url = saved_filename
    await db.commit()
    await db.refresh(app_record)
    return app_record

async def list_applications(db: AsyncSession, department: str = None) -> list[Application]:
    """Aktif başvuruları kronolojik olarak listeler, isteğe bağlı departman filtresi sunar."""
    query = select(Application).where(Application.is_deleted == False).order_by(Application.id.desc())
    
    if department:
        query = query.where(Application.department == department)
        
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_application_status(db: AsyncSession, app_id: int, payload: ApplicationStatusUpdate) -> Application:
    """Başvurunun statüsünü (İK süreç adımlarını) günceller."""
    query = select(Application).where(and_(Application.id == app_id, Application.is_deleted == False))
    result = await db.execute(query)
    app_record = result.scalar_one_or_none()
    
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Başvuru bulunamadı.")
        
    app_record.status = payload.status
    await db.commit()
    await db.refresh(app_record)
    return app_record