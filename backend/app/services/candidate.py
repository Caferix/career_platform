from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.candidate import Candidate, CandidateEducation, CandidateLanguage
from app.models.consents import Consent
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.core.security import hash_data

async def create_candidate(
    db: AsyncSession, 
    data: CandidateCreate, 
    ip_address: str, 
    is_communication_consented: bool = False
) -> Candidate:
    """
    Deterministik SHA-256 hash'i (hashed_phone) üzerinden mükerrer kontrolü yapar,
    veriyi property'ler aracılığıyla şifreler, alt tabloları ve rızaları atomic olarak kaydeder.
    """
    # 1. ADIM: Telefonun deterministik hash'ini üretiyoruz
    phone_search_hash = hash_data(data.phone)
    
    # 2. ADIM: Aramayı şifreli alanda değil, deterministik hash sütununda yapıyoruz
    query = select(Candidate).where(
        Candidate.hashed_phone == phone_search_hash,
        Candidate.is_deleted == False
    )
    result = await db.execute(query)
    existing = result.scalars().first()
    
    if existing:
        # Kural 8: Veri sızıntısını (User Enumeration) önlemek için jenerik hata
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Girilen bilgilerle daha önce işlem yapılmıştır. Lütfen kontrol edip tekrar deneyiniz."
        )
    
    try:
        # 3. ADIM: Nesneyi temizlenmiş düz verilerle besliyoruz (Setter'lar otomatik şifreleyecek)
        candidate = Candidate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,               
            phone=data.phone,               
            hashed_phone=phone_search_hash, # WHERE aramaları için indeksli alan
            birth_date=data.birth_date,
            nationality=data.nationality,
            marital_status=data.marital_status,
            driving_license=data.driving_license,
            gender=data.gender,
            city=data.city,
            district=data.district,
            address_detail=data.address_detail, 
            military_status=data.military_status,
            skills=data.skills,
            is_phone_verified=True
        )
        
        db.add(candidate)
        await db.flush()  # Alt tablolar için ID'yi ürettirip transaction'ı açık tutuyoruz
        
        # 4. ADIM: Çoklu Eğitim Geçmişi (Alt Tablo)
        if data.educations:
            for edu in data.educations:
                new_edu = CandidateEducation(
                    applicant_id=candidate.id,
                    education_level=edu.education_level,
                    school_name=edu.school_name,
                    department=edu.department,
                    graduation_year=edu.graduation_year
                )
                db.add(new_edu)
            
        # 5. ADIM: Çoklu Yabancı Dil Bilgisi (Alt Tablo)
        if data.languages:
            for lang in data.languages:
                new_lang = CandidateLanguage(
                    applicant_id=candidate.id,
                    language_name=lang.language_name,
                    level=lang.level
                )
                db.add(new_lang)

        # 6. ADIM: Hukuki Onaylar (Consents) - Sadece IP adresi ile
        kvkk_consent = Consent(
            applicant_id=candidate.id,
            consent_type="kvkk",
            consent_text_version="v2026.1",
            ip_address=ip_address,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(kvkk_consent)
        
        if is_communication_consented:
            comm_consent = Consent(
                applicant_id=candidate.id,
                consent_type="communication",
                consent_text_version="v2026.1",
                ip_address=ip_address,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(comm_consent)

        # 7. ADIM: DB Mühürleme
        await db.commit()
        await db.refresh(candidate)
        return candidate

    except Exception:
        await db.rollback()
        # Kural 8: Hata detayı gizlendi
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Aday profil kaydı esnasında sistem hatası oluştu."
        )

async def get_candidate(db: AsyncSession, candidate_id: int):
    """
    Belirtilen ID'ye sahip adayı, ilişkili alt tablolarıyla birlikte (selectinload)
    asenkron uyumlu olarak veritabanından çeker.
    """
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == candidate_id, Candidate.is_deleted == False)
        .options(
            selectinload(Candidate.applications),
            selectinload(Candidate.educations),
            selectinload(Candidate.languages)
        )
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Aday bulunamadı.")
        
    return candidate

async def list_candidates(db: AsyncSession, skip: int = 0, limit: int = 10) -> list[Candidate]:
    """Aktif adayları sayfalayarak listeler."""
    query = select(Candidate).where(Candidate.is_deleted == False).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_candidate(db: AsyncSession, candidate_id: int, data: CandidateUpdate) -> Candidate:
    """Adayı asenkron şifreleme kurallarına (Property Setter) göre günceller."""
    candidate = await get_candidate(db, candidate_id)
    update_dict = data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        if key == "phone":
            # Setter property otomatik şifreleyecek, biz sadece hash'i ayrıca güncelliyoruz
            candidate.phone = value 
            candidate.hashed_phone = hash_data(value)
        else:
            # Email, address_detail vb. gelirse de kendi setter'ları devreye girecek
            setattr(candidate, key, value)
            
    candidate.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(candidate)
    return candidate

async def delete_candidate(db: AsyncSession, candidate_id: int) -> None:
    """Yumuşak silme (Soft Delete) operasyonu."""
    candidate = await get_candidate(db, candidate_id)
    candidate.is_deleted = True
    candidate.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()