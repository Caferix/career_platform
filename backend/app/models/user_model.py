from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    login_name = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'hr' veya 'manager'
    department = Column(String(100), nullable=True)  # Sadece manager için, hr için null
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)