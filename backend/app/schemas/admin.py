from pydantic import BaseModel, Field
from typing import Optional, List

class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100, description="Departman adı")
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class PositionBase(BaseModel):
    name: str = Field(..., max_length=100, description="Pozisyon adı")
    is_active: bool = True

class PositionCreate(PositionBase):
    department_id: int

class PositionResponse(PositionBase):
    id: int
    department_id: int

    class Config:
        from_attributes = True

class DepartmentResponse(DepartmentBase):
    id: int
    positions: List[PositionResponse] = []

    class Config:
        from_attributes = True