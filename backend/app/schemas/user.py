from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    login_name: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., description="Kullanıcıya atanacak rol (Örn: admin, hr, manager)")
    department: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    login_name: str
    role: str
    department: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    login_name: str
    password: str