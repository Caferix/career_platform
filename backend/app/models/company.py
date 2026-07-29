from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, server_default="false")

    # ON DELETE CASCADE kesinlikle yok. İlişki seviyesinde yönetilecek.
    positions = relationship("Position", back_populates="department")

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, server_default="false")

    department = relationship("Department", back_populates="positions")