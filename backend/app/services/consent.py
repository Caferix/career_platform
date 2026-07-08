# app/services/consent.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.consents import Consent
from app.schemas.consent import ConsentCreate

async def save_consent(db: AsyncSession, payload: ConsentCreate, ip_address: str) -> Consent:
    """
    Adayın rıza (KVKK/İletişim) onayını asenkron olarak veritabanına kaydeder.
    """
    db_consent = Consent(
        applicant_id=payload.applicant_id,
        consent_type=payload.consent_type,
        consent_text_version=payload.consent_text_version,
        ip_address=ip_address
    )
    db.add(db_consent)
    await db.commit()
    await db.refresh(db_consent)
    return db_consent