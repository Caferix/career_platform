from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(100), nullable=True) # Örn: Hibrit, Onsite, Uzaktan
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Kural 8 uyumlu: Soft Delete
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at = Column(DateTime, nullable=True)

    # İlişkiler (Kural 12: CASCADE yok)
    department = relationship("Department")
    position = relationship("Position")
    created_by = relationship("User")
    applications = relationship("Application", back_populates="job_posting")