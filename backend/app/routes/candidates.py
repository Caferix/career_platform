from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse, ApplicationShortResponse
from app.services import candidate as candidate_service
from app.models.candidate import Candidate
from app.core.security import get_current_user
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/applicants", tags=["Applicants"])

@router.get("/me", response_model=CandidateResponse)
async def get_current_candidate_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    hashed_phone_from_token = current_user.get("sub")
    
    # 🌟 DÜZELTME 1: Sorguya 'selectinload(Candidate.applications)' ekleyerek 
    # adayın tüm ilişkili başvurularını tek seferde veritabanından canlı çekiyoruz.
    result = await db.execute(
        select(Candidate)
        .options(selectinload(Candidate.applications))
        .where(
            Candidate.hashed_phone == hashed_phone_from_token,
            Candidate.is_deleted == False
        )
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Aday profili bulunamadı.")

    # 🌟 DÜZELTME 2: Hardcode boş dizi yerine veritabanından gelen gerçek 
    # ve güncel başvuruları listesini Pydantic response modeline mühürlüyoruz.
    return CandidateResponse(
        id=candidate.id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,
        phone=candidate.phone,
        university=candidate.university,
        university_department=candidate.university_department,
        graduation_year=candidate.graduation_year,
        is_phone_verified=candidate.is_phone_verified,
        created_at=candidate.created_at,
        applications=candidate.applications # Canlı ilişkisel veri!
    )

@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_new_candidate(data: CandidateCreate, db: AsyncSession = Depends(get_db)):
    """Yeni bir aday profili oluşturur."""
    # 1. Servis adayı oluşturuyor ve veritabanına mühürlüyor
    candidate = await candidate_service.create_candidate(db=db, data=data)
    
    # MISSINGGREENLET FIX: Nesneyi doğrudan döndürmüyoruz. 
    # Henüz başvurusu olmayan yeni adayın verilerini elle şemaya dökerek Pydantic'in lazy-loading tetiklemesini engelliyoruz.
    return CandidateResponse(
        id=candidate.id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,  # @property çözülüyor
        phone=candidate.phone,  # @property çözülüyor
        hashed_phone=candidate.hashed_phone,
        university=candidate.university,
        university_department=candidate.university_department,
        graduation_year=candidate.graduation_year,
        is_phone_verified=candidate.is_phone_verified,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
        applications=[]  # Yeni kayıtta başvuru listesi boş başlar, veritabanına gitmeye zorlamaz!
    )

# 🌟 KURAL 2: Dinamik rota alt satırda olmalı ve yol parametresi SADECE integer kabul etmeli!
@router.get("/{candidate_id:int}", response_model=CandidateResponse)
async def get_candidate_by_id(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """ID değeri verilen aktif adayın detaylarını getirir."""
    return await candidate_service.get_candidate(db=db, candidate_id=candidate_id)

@router.get("/", response_model=list[CandidateResponse])
async def list_all_candidates(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Aktif adayları sayfalayarak listeler."""
    return await candidate_service.list_candidates(db=db, skip=skip, limit=limit)

@router.put("/{candidate_id:int}", response_model=CandidateResponse)
async def update_candidate_by_id(candidate_id: int, data: CandidateUpdate, db: AsyncSession = Depends(get_db)):
    """Belirtilen adayın bilgilerini günceller."""
    return await candidate_service.update_candidate(db=db, candidate_id=candidate_id, data=data)

@router.delete("/{candidate_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate_by_id(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """Adayı sistemde pasife çeker (Soft Delete). İçerik dönmez."""
    await candidate_service.delete_candidate(db=db, candidate_id=candidate_id)
    return None