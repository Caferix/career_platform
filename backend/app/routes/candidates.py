from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse
from app.services import candidate as candidate_service
from app.services.access_log import log_access
from app.core.security import require_hr, require_hr_or_manager

# Kurumsal URL isimlendirme standardı (Çoğul isim)
router = APIRouter(prefix="/applicants", tags=["Applicants"])

@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_new_candidate(data: CandidateCreate, db: AsyncSession = Depends(get_db)):
    """Yeni bir aday profili oluşturur."""
    return await candidate_service.create_candidate(db=db, data=data)

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate_by_id(
    candidate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr_or_manager),
):
    """ID değeri verilen aktif adayın detaylarını getirir."""
    candidate = await candidate_service.get_candidate(db=db, candidate_id=candidate_id)

    await log_access(
        db=db,
        user_id=current_user.get("user_id", 0),
        user_role=current_user.get("role", ""),
        action="viewed_candidate",
        target_id=candidate_id,
        ip_address=request.client.host if request.client else None,
    )

    return candidate

@router.get("/", response_model=list[CandidateResponse])
async def list_all_candidates(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_hr),
):
    """Aktif adayları sayfalayarak listeler."""
    return await candidate_service.list_candidates(db=db, skip=skip, limit=limit)

@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate_by_id(candidate_id: int, data: CandidateUpdate, db: AsyncSession = Depends(get_db)):
    """Belirtilen adayın bilgilerini günceller."""
    return await candidate_service.update_candidate(db=db, candidate_id=candidate_id, data=data)

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate_by_id(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """Adayı sistemde pasife çeker (Soft Delete). İçerik dönmez."""
    await candidate_service.delete_candidate(db=db, candidate_id=candidate_id)
    return None