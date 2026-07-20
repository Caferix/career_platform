# app/routes/consents.py
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.consent import ConsentCreate, ConsentResponse
from app.services import consent as consent_service
from app.core.security import get_current_user  # Güvenlik katmanını import et

router = APIRouter(prefix="/consents", tags=["Consents"])

@router.post("/", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def create_consent_record(
    payload: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  #  Token zorunluluğunu mühürle!
):
    """
    Adayın verdiği rıza onayını (KVKK veya İletişim) IP adresiyle birlikte sisteme mühürler.
    """
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    return await consent_service.save_consent(db=db, payload=payload, ip_address=ip_address, user_agent=user_agent)