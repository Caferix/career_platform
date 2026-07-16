from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime, date

# --- Alt İlişkisel Şemalar (Eğitim ve Dil) ---

class EducationSchema(BaseModel):
    education_level: Literal["İlkokul", "Lise", "Önlisans", "Lisans", "Yüksek Lisans", "Doktora"]
    school_name: str = Field(..., min_length=2, max_length=150)
    department: Optional[str] = Field(None, max_length=150)
    graduation_year: Optional[int] = Field(None, ge=1980, le=2040)

    model_config = {"from_attributes": True}

class LanguageSchema(BaseModel):
    language_name: str = Field(..., min_length=2, max_length=50)
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2"]

    model_config = {"from_attributes": True}


# --- Tekil Eğitim/Dil Ekleme-Silme İçin Response Şemaları ---
# (POST /applicants/{id}/educations ve /languages endpoint'lerinin dönüş tipi)

class EducationResponse(EducationSchema):
    id: int
    applicant_id: int

    model_config = {"from_attributes": True}

class LanguageResponse(LanguageSchema):
    id: int
    applicant_id: int

    model_config = {"from_attributes": True}


# --- GELEN VERİ (Request) ---

class CandidateCreate(BaseModel):
    """Aday ilk kez dev formu doldururken frontend'den gelecek veri yapısı."""
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)

    # Yeni profil alanları
    birth_date: Optional[date] = Field(None, description="Takvimden seçilen doğum tarihi")
    nationality: str = Field("T.C.", max_length=50)
    marital_status: Optional[Literal["Evli", "Bekar"]] = None
    driving_license: Optional[str] = Field(None, max_length=50, description="Çoklu seçim: 'B, C' gibi")
    gender: Optional[Literal["Kadın", "Erkek"]] = None

    # Adres bilgileri
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=100)
    address_detail: Optional[str] = Field(None, description="Şifrelenecek açık adres")

    # Dinamik alanlar
    military_status: Optional[Literal["Yapıldı", "Muaf", "Tecilli"]] = None
    skills: Optional[str] = Field(None, description="Virgülle ayrılmış yetenekler")

    # Birden fazla eklenebilecek alt listeler
    educations: list[EducationSchema] = Field(default=[], description="Eğitim geçmişi listesi")
    languages: list[LanguageSchema] = Field(default=[], description="Yabancı dil geçmişi listesi")


class CandidateUpdate(BaseModel):
    """Adayın daha sonra profil sayfasında güncelleyebileceği alanlar."""
    first_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    marital_status: Optional[Literal["Evli", "Bekar"]] = None
    driving_license: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=50)
    district: Optional[str] = Field(default=None, max_length=100)
    address_detail: Optional[str] = Field(default=None)
    military_status: Optional[Literal["Yapıldı", "Muaf", "Tecilli"]] = None
    skills: Optional[str] = Field(default=None)

    # Profil güncellerken eğitim ve diller de komple yenilenebilir
    educations: Optional[list[EducationSchema]] = None
    languages: Optional[list[LanguageSchema]] = None


# --- DÖNEN VERİ (Response) ---

class ApplicationShortResponse(BaseModel):
    id: int
    position: str
    department: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateResponse(BaseModel):
    """API dış dünyaya adayı dönerken kullanılacak tam kurumsal model."""
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    driving_license: Optional[str] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address_detail: Optional[str] = None
    military_status: Optional[str] = None
    skills: Optional[str] = None
    is_phone_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # İlişkisel alt listelerin dışarıya açılması
    educations: list[EducationSchema] = []
    languages: list[LanguageSchema] = []
    applications: list[ApplicationShortResponse] = []

    model_config = {"from_attributes": True}