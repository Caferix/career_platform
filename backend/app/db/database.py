from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.settings import settings

# Kural 5 ve 11: Bağlantı tek yerden ve .env'den gelen gizli URL ile kurulur
DATABASE_URL = settings.DATABASE_URL

# Veritabanı asenkron motoru
engine = create_async_engine(DATABASE_URL, echo=True)

# Oturum (Session) fabrikası
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Tüm SQLAlchemy modellerimizin türeyeceği ana sınıf
Base = declarative_base()

# Bağımlılık Enjeksiyonu (Dependency Injection) için DB oturum yöneticisi
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()