from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.db.database import Base

class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(255), nullable=False) # Şifreli telefon formatı gelecek
    code = Column(String(6), nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    is_used = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    
    # Kural 13: ON DELETE CASCADE KESİNLİKLE YOK
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    
    consent_type = Column(String(50), nullable=False)          # 'kvkk', 'iletisim'
    consent_text_version = Column(String(10), nullable=False)  # 'v1.0'
    ip_address = Column(String(45), nullable=True)             # IPv6 destekli 45 karakter
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Kural 9: consents tablosundan ASLA VERİ SİLİNMEZ. 
    # Bu yüzden is_deleted veya deleted_at alanları buraya eklenmez!


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    user_role = Column(String(20), nullable=False) # 'hr', 'manager', 'applicant'
    action = Column(String(50), nullable=False)    # 'viewed_candidate'
    target_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Kural 9: access_logs tablosundan ASLA VERİ SİLİNMEZ.
    # Müfettiş denetimleri için bu veri ömür boyu kalıcıdır. Soft delete eklenmez.