from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.database import get_db
from app.models.job_posting import JobPosting
from app.schemas.job_posting import JobPostingResponse

router = APIRouter(prefix="/public/jobs", tags=["Public Job Postings"])

@router.get("", response_model=list[JobPostingResponse])
async def list_public_job_postings(db: AsyncSession = Depends(get_db)):
    """
    Sistemde yayında olan (is_active=True ve is_deleted=False) tüm ilanları getirir.
    Kimlik doğrulaması gerektirmez, herkes erişebilir.
    """
    stmt = (
        select(JobPosting)
        .where(
            JobPosting.is_active == True,
            JobPosting.is_deleted == False
        )
        .order_by(JobPosting.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_public_job_detail(
    job_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Spesifik bir yayındaki ilanın detay bilgilerini getirir.
    İlan yoksa, pasifse veya silinmişse 404 döner.
    """
    stmt = select(JobPosting).where(
        JobPosting.id == job_id,
        JobPosting.is_active == True,
        JobPosting.is_deleted == False
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aradığınız ilan bulunamadı veya artık yayında değil."
        )

    return job