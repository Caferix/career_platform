from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.core.security import encrypt_data, decrypt_data
from typing import Optional, Literal

class Candidate(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    
    # Kural 15: E-posta ve telefon şifreli (encrypted) saklanır.
    # Veritabanında gerçek sütun isimleri 'email' ve 'phone' olacak ancak 
    # biz kod içinde bunlara getter/setter (property) üzerinden erişeceğiz.
    _email = Column("email", String(255), nullable=False)
    _phone = Column("phone", String(255), nullable=False, unique=True, index=True)
    
    university = Column(String(100), nullable=True)
    university_department = Column(String(100), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    
    is_phone_verified = Column(Boolean, nullable=False, default=False)
    
    # Kural 8: Kayıt silinmez, is_deleted ile işaretlenir (Soft Delete)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Kural 13: ON DELETE CASCADE kullanılmaz! 
    # İlişkili verilerin silinme yönetimini veritabanına bırakmıyoruz, kod seviyesinde kontrollü yapıyoruz.
    applications = relationship("Application", back_populates="candidate")
    ApplicationStatus = Literal["pending", "under_review", "accepted", "rejected"]

    # --- Şifreleme Kapsülleme (Getter / Setter) Mekanizması ---
    @property
    def email(self) -> str:
        """Veritabanından şifreli veriyi okurken otomatik olarak çözer (Decrypt)."""
        return decrypt_data(self._email)

    @email.setter
    def email(self, value: str):
        """Koda düz metin girildiğinde veritabanına şifreleyerek yazar (Encrypt)."""
        self._email = encrypt_data(value)

    @property
    def phone(self) -> str:
        """Veritabanından şifreli telefonu okurken otomatik olarak çözer."""
        return decrypt_data(self._phone)

    @phone.setter
    def phone(self, value: str):
        """Koda düz telefon girildiğinde şifreleyerek kaydeder."""
        self._phone = encrypt_data(value)


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Kural 13: ON DELETE CASCADE yok.
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    
    position = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    experience_years = Column(Integer, nullable=True)
    notes = Column(String(500), nullable=True)
    cv_url = Column(String(255), nullable=True)
    
    # Kural 14: status alanı enum değil VARCHAR, Pydantic'te kontrol edilir
    status = Column(String(20), nullable=False, default="pending")
    
    # Kural 8: Soft Delete Alanları
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Aday tablosuna geri bağlantı
    candidate = relationship("Candidate", back_populates="applications")

    