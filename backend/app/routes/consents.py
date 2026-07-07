from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.settings import settings
from app.db.database import get_db
from app.schemas.consent import ConsentCreate
from app.services.candidate import get_candidate_by_phone
from app.services.consent import save_consent

router = APIRouter(prefix="/consents", tags=["Consents"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_consent(
    payload: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "applicant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz bulunmamaktadır."
        )

    phone = current_user.get("phone")
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kimlik doğrulama bilgisi eksik."
        )

    applicant = await get_candidate_by_phone(db, phone)
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aday kaydı bulunamadı."
        )

    return await save_consent(
        db=db,
        applicant_id=applicant.id,
        consent_type=payload.consent_type,
        consent_text_version=settings.CONSENT_TEXT_VERSION,
        ip_address=request.client.host if request.client else None,
    )