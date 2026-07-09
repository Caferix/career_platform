from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional

from app.models.candidate import Candidate
from app.schemas.candidate import CandidateCreate, CandidateUpdate
# Asenkron şifreleme ve hash motorlarımızı import ediyoruz
from app.core.security import encrypt_data, hash_data

async def create_candidate(db: AsyncSession, data: CandidateCreate) -> Candidate:
    """
    Deterministik SHA-256 hash'i (hashed_phone) üzerinden mükerrer kontrolü yapar,
    veriyi asenkron şifreleyerek güvenli kaydeder.
    """
    # 1. ADIM: Telefonun deterministik hash'ini asenkron üretiyoruz
    phone_search_hash = hash_data(data.phone)
    
    # 2. ADIM: Aramayı şifreli alanda değil, deterministik hash sütununda yapıyoruz!
    query = select(Candidate).where(
        Candidate.hashed_phone == phone_search_hash,
        Candidate.is_deleted == False
    )
    result = await db.execute(query)
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Bu telefon numarası zaten kayıtlı."
        )
    
    # 3. ADIM: Hassas verileri asenkron motorla şifreliyoruz
    encrypted_phone = encrypt_data(data.phone)
    encrypted_email = encrypt_data(data.email)
    
    # 4. ADIM: Nesneyi temizlenmiş şifreli verilerle besliyoruz (Setter yok, doğrudan atama)
    candidate = Candidate(
        first_name=data.first_name,
        last_name=data.last_name,
        university=data.university,
        university_department=data.university_department,
        graduation_year=data.graduation_year,
        _email=encrypted_email,       # Modeldeki şifreli gerçek kolonlar
        _phone=encrypted_phone,       # Modeldeki şifreli gerçek kolonlar
        hashed_phone=phone_search_hash # WHERE aramaları için indeksli alan
    )

    # 5. ADIM: DB mühürleme
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate

async def get_candidate(db: AsyncSession, candidate_id: int):
    """
    Belirtilen ID'ye sahip adayı, ilişkili başvurularıyla birlikte (selectinload)
    asenkron uyumlu olarak veritabanından çeker.
    """
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == candidate_id, Candidate.is_deleted == False)
        .options(selectinload(Candidate.applications))  # 🌟 LAZY LOADING PATLAMASINI BİTİREN SATIR
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
    """Adayı asenkron şifreleme kurallarına göre günceller."""
    candidate = await get_candidate(db, candidate_id)
    update_dict = data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        if key == "email":
            candidate._email = encrypt_data(value)
        elif key == "phone":
            candidate._phone = encrypt_data(value)
            candidate.hashed_phone = hash_data(value)
        else:
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