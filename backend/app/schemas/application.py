from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

# Kural 13: Statüleri kod seviyesinde katılaştırıyoruz
ApplicationStatus = Literal["Draft", "Applied", "Under_Review", "Accepted", "Rejected"]

class ApplicationCreate(BaseModel):
    """Adayın bir pozisyona ilk başvuruyu yaparken göndereceği veri modeli."""
    applicant_id: int = Field(..., description="Başvuran adayın ID'si")
    position: str = Field(..., max_length=100, min_length=2, description="Başvurulan pozisyon (Örn: Android Developer)")
    department: str = Field(..., max_length=100, min_length=2, description="İlgili departman (Örn: Mobil Yazılım)")
    experience_years: int = Field(..., ge=0, description="Yıl bazında deneyim süresi")
    notes: Optional[str] = Field(None, max_length=500, description="Adayın başvuru esnasında eklemek istediği notlar")

class ApplicationStatusUpdate(BaseModel):
    """İK yetkilisinin başvuru sürecini güncellerken kullanacağı model."""
    status: ApplicationStatus

class ApplicationResponse(BaseModel):
    """İstemciye güvenli bir şekilde döneceğimiz başvuru çıktı modeli."""
    id: int
    applicant_id: int
    position: str
    department: str
    experience_years: int
    notes: Optional[str]
    status: str
    cv_url: Optional[str] = None 
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy objelerini otomatik Pydantic modeline dönüştürür (ORM mode)