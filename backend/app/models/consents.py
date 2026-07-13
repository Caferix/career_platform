# app/models/consents.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base

class Consent(Base):
    """
    Adayların başvuru esnasında onayladığı KVKK ve İletişim rızalarını tutan tablo.
    İleride olası hukuksal denetimler için kanıt niteliğindedir.
    """
    __tablename__ = "consents"
    # 🌟 Hot reload ve mükerrer import esnasında metadata çakışmasını engelleyen emniyet kilidi:
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, nullable=False, index=True)
    consent_type = Column(String(20), nullable=False)  # 'kvkk' veya 'communication'
    consent_text_version = Column(String(50), nullable=False, default="v2026.1")
    ip_address = Column(String(45), nullable=False)    # IPv4 veya IPv6 destekli uzunluk
    # Onayı yapan tarayıcı ve cihaz bilgilerini loglamak için
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    

class AccessLog(Base):
    """
    İK ve Departman Yöneticilerinin hassas kişisel verilere (Örn: CV indirme)
    erişimini izleyen KVKK denetim izi tablosu. Güvenlik gereği silme operasyonu içermez.
    """
    __tablename__ = "access_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_role = Column(String(20), nullable=False)
    action = Column(String(50), nullable=False)       # 'downloaded_cv', 'updated_status' vb.
    target_id = Column(Integer, nullable=False)       # İşlem yapılan başvuru veya aday ID'si
    ip_address = Column(String(45), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)