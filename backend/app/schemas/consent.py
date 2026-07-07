from pydantic import BaseModel, Field
from typing import Literal


class ConsentCreate(BaseModel):
    consent_type: Literal["kvkk", "iletisim"] = Field(..., description="Onay türü")