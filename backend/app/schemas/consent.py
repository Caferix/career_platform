from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ConsentCreate(BaseModel):
    applicant_id: int = Field(..., description="Rızayı veren adayın ID'si")
    consent_type: str = Field(..., description="'kvkk' veya 'communication'")
    consent_text_version: str = Field("v2026.1", description="Onaylanan metnin versiyonu")
    user_agent: Optional[str] = Field(None, description="Onay veren cihazın tarayıcı bilgisi")

class ConsentResponse(BaseModel):
    id: int
    applicant_id: int
    consent_type: str
    consent_text_version: str
    ip_address: str
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True