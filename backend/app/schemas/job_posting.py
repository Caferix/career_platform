from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# --- OLUŞTURMA (Create) ---
class JobPostingCreate(BaseModel):
    position_id: int = Field(..., description="İlanın ait olduğu pozisyon ID'si")
    title: str = Field(..., min_length=3, max_length=150, description="İlan başlığı")
    description: str = Field(..., min_length=10, description="İlan detaylı açıklaması")
    location: Optional[str] = Field(None, max_length=100, description="Çalışma modeli/Lokasyon (Örn: Hibrit, Onsite)")
    expires_at: Optional[datetime] = Field(None, description="Son başvuru tarihi (Opsiyonel)")

# --- GÜNCELLEME (Update) ---
class JobPostingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, min_length=10)
    location: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

# --- YANIT (Response - Dışarıya Dönen) ---
class JobPostingResponse(BaseModel):
    id: int
    department_id: int
    position_id: int
    created_by_user_id: int
    title: str
    description: str
    location: Optional[str] = None
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}