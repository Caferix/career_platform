import hashlib
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.db.database import Base
from app.core.security import encrypt_data, decrypt_data
from typing import Optional, Literal

class Candidate(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    
    # Kural 15: Hassas kişisel veriler (PII) şifreli saklanır.
    _email = Column("email", String(255), nullable=True)
    _phone = Column("phone", String(255), nullable=False, unique=True, index=True)
    hashed_phone = Column(String(64), nullable=False, index=True)
    
    #  Yeni Kişisel ve Profil Alanları (Düz Metin & Doğru Tipler)
    birth_date = Column(Date, nullable=True) # Takvim seçimi için saf Date
    nationality = Column(String(50), nullable=True)
    marital_status = Column(String(10), nullable=True) # Evli / Bekar (Pydantic kontrollü)
    driving_license = Column(String(50), nullable=True) # Çoklu seçim: "B, C" gibi virgülle ayrılmış
    gender = Column(String(10), nullable=True) # Kadın / Erkek
    
    #  Adres Alanları (Şehir/İlçe arama için düz metin, açık adres şifreli)
    city = Column(String(50), nullable=True)
    district = Column(String(100), nullable=True)
    _address_detail = Column("address_detail", Text, nullable=True) # Kural 15: Fernet Encrypt
    
    #  Askerlik Durumu (Erkek adaylar için dinamik)
    military_status = Column(String(20), nullable=True) # Yapıldı, Muaf, Tecilli
    
    #  Yetenekler / Nitelikler
    skills = Column(Text, nullable=True) # Virgülle ayrılmış serbest metin
    social_links = Column(JSONB, nullable=True)
    is_phone_verified = Column(Boolean, nullable=False, default=False)
    
    # Kural 8: Soft Delete
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc).replace(tzinfo=None), onupdate=datetime.utcnow)

    # İlişkiler (Kural 13: ON DELETE CASCADE yok, kod seviyesinde silinecek)
    applications = relationship("Application", back_populates="candidate")
    educations = relationship("CandidateEducation", back_populates="candidate")
    languages = relationship("CandidateLanguage", back_populates="candidate")

    # --- Şifreleme Kapsülleme (Getter / Setter) Mekanizması ---
    @property
    def email(self) -> str:
        return decrypt_data(self._email)

    @email.setter
    def email(self, value: str):
        self._email = encrypt_data(value)

    @property
    def phone(self) -> str:
        return decrypt_data(self._phone)

    @phone.setter
    def phone(self, value: str):
        self._phone = encrypt_data(value)

    @property
    def address_detail(self) -> Optional[str]:
        """Açık adresi veritabanından okurken otomatik çözer."""
        if self._address_detail:
            return decrypt_data(self._address_detail)
        return None

    @address_detail.setter
    def address_detail(self, value: Optional[str]):
        """Düz metin açık adresi veritabanına şifreleyerek yazar."""
        if value:
            self._address_detail = encrypt_data(value)
        else:
            self._address_detail = None


class CandidateEducation(Base):
    """ Yeni Tablo: Adayın birden fazla eğitim bilgisini tutar."""
    __tablename__ = "candidate_educations"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    
    education_level = Column(String(50), nullable=False) # İlkokul, Lise, Lisans, Yüksek Lisans
    school_name = Column(String(150), nullable=False) # Okul / Üniversite adı
    department = Column(String(150), nullable=True) # Bölüm / Alan (İlkokul için null olabilir)
    graduation_year = Column(Integer, nullable=True) # Mezuniyet / Beklenen yıl

    candidate = relationship("Candidate", back_populates="educations")


class CandidateLanguage(Base):
    """ Yeni Tablo: Adayın birden fazla yabancı dil bilgisini tutar."""
    __tablename__ = "candidate_languages"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    
    language_name = Column(String(50), nullable=False) # İngilizce, Almanca vb.
    level = Column(String(10), nullable=False) # A1, A2, B1, B2, C1, C2

    candidate = relationship("Candidate", back_populates="languages")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)

    # İş ilanına özel başvuru bağlantısı
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    
    position = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    
    #  Deneyim Alanları (Yıl ayrı, detay serbest metin)
    experience_years = Column(Integer, nullable=True)
    experience_detail = Column(Text, nullable=True) # Nerede ne yaptığının özeti
    
    #  Adı değişen ve tipi genişleyen sütun: notes -> cover_letter
    cover_letter = Column(Text, nullable=True) 
    
    #  Referans Alanları (Şirket içi referansın iletişim bilgisi şifreli)
    reference_name = Column(String(100), nullable=True) # Referans Ad-Soyad
    reference_position = Column(String(100), nullable=True) # Referans Pozisyon
    _reference_contact = Column("reference_contact", Text, nullable=True) # Kural 15: Şifreli iletişim bilgisi
    
    cv_url = Column(String(255), nullable=True)
    
    # Kural 14: status VARCHAR, Pydantic'te kontrol edilir
    status = Column(String(20), nullable=False, default="pending")
    
    # Kural 8: Soft Delete Alanları
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="applications")
    job_posting = relationship("JobPosting", back_populates="applications")  #job posting ilişkisi

    @property
    def reference_contact(self) -> Optional[str]:
        if self._reference_contact:
            return decrypt_data(self._reference_contact)
        return None

    @reference_contact.setter
    def reference_contact(self, value: Optional[str]):
        if value:
            self._reference_contact = encrypt_data(value)
        else:
            self._reference_contact = None