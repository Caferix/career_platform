from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_models import Consent


async def save_consent(
    db: AsyncSession,
    applicant_id: int,
    consent_type: str,
    consent_text_version: str,
    ip_address: str | None,
) -> Consent:
    consent = Consent(
        applicant_id=applicant_id,
        consent_type=consent_type,
        consent_text_version=consent_text_version,
        ip_address=ip_address,
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent