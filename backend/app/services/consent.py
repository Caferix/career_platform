# app/services/consent.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.consents import Consent
from app.schemas.consent import ConsentCreate
from datetime import datetime
from sqlalchemy.future import select

async def save_consent(db: AsyncSession, payload: ConsentCreate, ip_address: str, user_agent: str):
    """
    Adayın verdiği rızayı veritabanına mühürler. 
    Eğer aday zaten aynı rıza tipine (KVKK veya iletişim) aktif bir onay vermişse,
    mükerrer satır oluşturmaz; mevcut satırın zaman damgasını ve IP'sini günceller (Upsert).
    """
    # 1. Veritabanında adayın aynı tipte aktif bir onayı var mı sorgula
    query = select(Consent).where(
        Consent.applicant_id == payload.applicant_id,
        Consent.consent_type == payload.consent_type,
        Consent.is_active == True
    )
    result = await db.execute(query)
    existing_consent = result.scalar_one_or_none()

    if existing_consent:
        # Mükerrer kaydı engelle, mevcut kaydı tazele
        existing_consent.created_at = datetime.utcnow()
        existing_consent.ip_address = ip_address
        existing_consent.user_agent = user_agent
        existing_consent.consent_text_version = payload.consent_text_version
        
        await db.commit()
        await db.refresh(existing_consent)
        return existing_consent
    
    # 2. Eğer ilk defa onay veriyorsa yeni kayıt aç
    new_consent = Consent(
        applicant_id=payload.applicant_id,
        consent_type=payload.consent_type,
        consent_text_version=payload.consent_text_version,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(new_consent)
    await db.commit()
    await db.refresh(new_consent)
    return new_consent