from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

ApplicationStatus = Literal["Draft", "Applied", "Under_Review", "Accepted", "Rejected"]

class ApplicationCreate(BaseModel):
    """Adayın bir pozisyona ilk başvuruyu yaparken göndereceği veri modeli."""
    applicant_id: int = Field(..., description="Başvuran adayın ID'si")
    job_posting_id: Optional[int] = Field(None, description="Başvurulan ilanın ID'si")
    position: str = Field(..., max_length=100, min_length=2, description="Başvurulan pozisyon (Örn: Android Developer)")
    department: str = Field(..., max_length=100, min_length=2, description="İlgili departman (Örn: Mobil Yazılım)")
    experience_years: int = Field(..., ge=0, description="Yıl bazında deneyim süresi")
    
    # Yeni eklenen alanlar
    experience_detail: Optional[str] = Field(None, description="Nerede ne yaptığının kısa özeti")
    cover_letter: Optional[str] = Field(None, description="Adayın başvuru esnasında eklemek istediği ön yazı")
    
    # Yeni referans alanları
    reference_name: Optional[str] = Field(None, max_length=100, description="Referans olan kişinin adı soyadı")
    reference_position: Optional[str] = Field(None, max_length=100, description="Referansın şirketteki pozisyonu")
    reference_contact: Optional[str] = Field(None, description="Referansın şifrelenecek olan iletişim bilgisi")

class ApplicationStatusUpdate(BaseModel):
    """İK yetkilisinin başvuru sürecini güncellerken kullanacağı model."""
    status: ApplicationStatus

class ApplicationResponse(BaseModel):
    """İstemciye güvenli bir şekilde döneceğimiz başvuru çıktı modeli."""
    id: int
    applicant_id: int
    job_posting_id: Optional[int] = None
    position: str
    department: str
    experience_years: int
    experience_detail: Optional[str] = None
    cover_letter: Optional[str] = None
    reference_name: Optional[str] = None
    reference_position: Optional[str] = None
    reference_contact: Optional[str] = None
    status: str
    cv_url: Optional[str] = None
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True