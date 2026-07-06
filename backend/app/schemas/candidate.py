from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- GELEN VERİ (Request) ---

class CandidateCreate(BaseModel):
    """Yeni aday oluştururken API'ye gönderilecek veri."""
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    university: Optional[str] = Field(None, max_length=100)
    university_department: Optional[str] = Field(None, max_length=100)
    graduation_year: Optional[int] = Field(None, ge=2000, le=2030)

class CandidateUpdate(BaseModel):
    # default=None diyerek bu alanların gönderilmesinin zorunlu olmadığını belirtiyoruz.
    # Gönderilmeyen alanlar veritabanında eski halini korur, bozulmaz.
    first_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    university: Optional[str] = Field(default=None, max_length=100)
    university_department: Optional[str] = Field(default=None, max_length=100)
    graduation_year: Optional[int] = Field(default=None, ge=2000, le=2030)

# --- DÖNEN VERİ (Response) ---

class CandidateResponse(BaseModel):
    """API'den kullanıcıya döndürülecek veri."""
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    university: Optional[str]
    university_department: Optional[str]
    graduation_year: Optional[int]
    is_phone_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}