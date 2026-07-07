from pydantic import BaseModel, Field
from typing import Optional

class UserCreate(BaseModel):
    login_name: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., description="'hr' veya 'manager'")
    department: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    login_name: str
    role: str
    department: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    login_name: str = Field(..., description="Kurumsal kullanici adi")
    password: str = Field(..., description="Sifre")