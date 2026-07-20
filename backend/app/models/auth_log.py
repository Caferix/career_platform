from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base

class FailedLoginAttempt(Base):
    __tablename__ = "failed_login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    login_name = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False) # IPv6 adreslerini de destekleyecek uzunlukta
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)