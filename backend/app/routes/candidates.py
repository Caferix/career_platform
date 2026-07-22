from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateResponse,
    EducationSchema, LanguageSchema, EducationResponse, LanguageResponse
)
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
    
    # Yeni eklenen alt tabloları (eğitim ve dil) lazy-loading hatasına karşı önden yüklüyoruz
    result = await db.execute(
        select(Candidate)
        .options(
            selectinload(Candidate.applications),
            selectinload(Candidate.educations),
            selectinload(Candidate.languages)
        )
        .where(
            Candidate.hashed_phone == hashed_phone_from_token,
            Candidate.is_deleted == False
        )
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Aday profili bulunamadı.")

    # Tüm ilişkiler önden yüklendiği için doğrudan SQLAlchemy modelini dönebiliriz.
    # Pydantic (from_attributes=True) bunu hatasız parse edecektir.
    return candidate

@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def complete_new_candidate(
    request: Request,
    data: CandidateCreate, 
    is_communication_consented: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Token bağımlılığı eklendi
):
    """Gölge adayın profil bilgilerini tamamlar (giydirir) ve kalan rızaları mühürler."""
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    # Token'dan adayın gerçek ID'sini alıyoruz
    candidate_id = current_user.get("user_id") # verify-otp'de token'a "user_id" olarak gömdük
    
    # 1. Servisimiz gölge adayı güncelleyip eğitim/dil/rızaları bağlayacak
    candidate = await candidate_service.complete_shadow_candidate(
        db=db, 
        candidate_id=candidate_id,
        data=data, 
        ip_address=ip_address,
        user_agent=user_agent,
        is_communication_consented=is_communication_consented
    )
    
    # MISSINGGREENLET FIX: Henüz başvurusu olmayan yeni adayın verilerini Pydantic'e döküyoruz
    return CandidateResponse(
        id=candidate.id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,  
        phone=candidate.phone,  
        hashed_phone=candidate.hashed_phone,
        birth_date=candidate.birth_date,
        nationality=candidate.nationality,
        marital_status=candidate.marital_status,
        driving_license=candidate.driving_license,
        gender=candidate.gender,
        city=candidate.city,
        district=candidate.district,
        address_detail=candidate.address_detail,
        military_status=candidate.military_status,
        skills=candidate.skills,
        is_phone_verified=candidate.is_phone_verified,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
        applications=[], # Yeni kayıtta başvuru boştur
        educations=data.educations, # Payload'dan aynen geçiriyoruz
        languages=data.languages  # Payload'dan aynen geçiriyoruz
    )

@router.get("/{candidate_id:int}", response_model=CandidateResponse)
async def get_candidate_by_id(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """ID değeri verilen aktif adayın detaylarını getirir."""
    return await candidate_service.get_candidate(db=db, candidate_id=candidate_id)

@router.get("/", response_model=list[CandidateResponse])
async def list_all_candidates(
    skip: int = 0, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 🌟 Token doğrulama bariyeri eklendi
):
    """
    Aktif adayları yetki ve departman filtresine göre 
    servis katmanında işleyerek asenkron listeler.
    """
    # Rota seviyesinde if-else kalabalığı yapmadan veriyi doğrudan servise delege ediyoruz
    return await candidate_service.list_candidates(
        db=db, 
        skip=skip, 
        limit=limit, 
        current_user=current_user
    )

@router.put("/{candidate_id:int}", response_model=CandidateResponse)
async def update_candidate_by_id(candidate_id: int, data: CandidateUpdate, db: AsyncSession = Depends(get_db)):
    """Belirtilen adayın bilgilerini günceller."""
    return await candidate_service.update_candidate(db=db, candidate_id=candidate_id, data=data)

@router.delete("/{candidate_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate_by_id(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """Adayı sistemde pasife çeker (Soft Delete). İçerik dönmez."""
    await candidate_service.delete_candidate(db=db, candidate_id=candidate_id)
    return None


# --- EĞİTİM: EKLEME / SİLME ---

@router.post("/{candidate_id:int}/educations", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def add_candidate_education(candidate_id: int, data: EducationSchema, db: AsyncSession = Depends(get_db)):
    """profile.html'deki 'Eğitim Ekle' formunun gönderdiği isteği karşılar."""
    return await candidate_service.add_education(db=db, candidate_id=candidate_id, data=data)


@router.delete("/educations/{edu_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_candidate_education(edu_id: int, db: AsyncSession = Depends(get_db)):
    """profile.html'deki eğitim satırındaki '✕' butonunun gönderdiği isteği karşılar."""
    await candidate_service.delete_education(db=db, edu_id=edu_id)
    return None


# --- DİL: EKLEME / SİLME ---

@router.post("/{candidate_id:int}/languages", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED)
async def add_candidate_language(candidate_id: int, data: LanguageSchema, db: AsyncSession = Depends(get_db)):
    """profile.html'deki 'Dil Ekle' formunun gönderdiği isteği karşılar."""
    return await candidate_service.add_language(db=db, candidate_id=candidate_id, data=data)


@router.delete("/languages/{lang_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_candidate_language(lang_id: int, db: AsyncSession = Depends(get_db)):
    """profile.html'deki dil satırındaki '✕' butonunun gönderdiği isteği karşılar."""
    await candidate_service.delete_language(db=db, lang_id=lang_id)
    return None