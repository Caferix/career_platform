from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.candidate import Candidate
# Dikkat: import yolunu 'app.schemas' olarak kurumsal standartta sabitledik
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.core.security import encrypt_data

# Adım 1-6: Senin başlattığın create_candidate fonksiyonunun asenkron hali
async def create_candidate(db: AsyncSession, data: CandidateCreate) -> Candidate:
    # Adım 1-2: Aynı telefon var mı? (Asenkron select sorgusu)
    query = select(Candidate).where(
        Candidate._phone == encrypt_data(data.phone),
        Candidate.is_deleted == False
    )
    result = await db.execute(query)
    existing = result.scalars().first()
    
    if existing:
        # Kural 7: 409 Conflict hata kodu
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Bu telefon numarası zaten kayıtlı."
        )
    
    # Adım 3-4: Şifrele ve nesne oluştur 
    candidate = Candidate(
        first_name=data.first_name,
        last_name=data.last_name,
        university=data.university,
        university_department=data.university_department,
        graduation_year=data.graduation_year
    )
    candidate.email = data.email  # modeldeki setter otomatik şifreler
    candidate.phone = data.phone  # modeldeki setter otomatik şifreler

    # Adım 5-6: Kaydet ve dön (Asenkron await eklendi)
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate

async def get_candidate(db: AsyncSession, candidate_id: int) -> Candidate:
    """ID ile aktif adayı getirir. Kural 8: is_deleted filtresi içerir."""
    query = select(Candidate).where(
        Candidate.id == candidate_id,
        Candidate.is_deleted == False
    )
    result = await db.execute(query)
    candidate = result.scalars().first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Aday bulunamadı."
        )
    return candidate


async def list_candidates(db: AsyncSession, skip: int = 0, limit: int = 10) -> list[Candidate]:
    """Aktif adayları sayfalayarak listeler. Kural 8 filtresi içerir."""
    query = select(Candidate).where(Candidate.is_deleted == False).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_candidate(db: AsyncSession, candidate_id: int, data: CandidateUpdate) -> Candidate:
    """Adayı günceller. Sadece gönderilen (None olmayan) alanları işler."""
    candidate = await get_candidate(db, candidate_id)
    
    # Pydantic v2 dump mekanizması ile sadece gelen verileri ayıklıyoruz
    update_dict = data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        if key == "email":
            candidate.email = value  # setter şifreler
        elif key == "phone":
            candidate.phone = value  # setter şifreler
        else:
            setattr(candidate, key, value)
            
    candidate.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def delete_candidate(db: AsyncSession, candidate_id: int) -> None:
    """Kural 8: Kayıt veritabanından silinmez, is_deleted ile işaretlenir (Soft Delete)."""
    candidate = await get_candidate(db, candidate_id)
    
    candidate.is_deleted = True
    candidate.deleted_at = datetime.utcnow()
    
    await db.commit()