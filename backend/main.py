from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

app = FastAPI(
    title="Career Platform API",
    description="Asynchronous Recruitment and Applicant Tracking System",
    version="1.0.0"
)

# Docker'daki veritabanımızın bağlantı adresi
DATABASE_URL = "postgresql+asyncpg://career_admin:career_secure_password_2026@localhost:5432/career_platform_prod"

@app.get("/")
async def root():
    return {
        "message": "Welcome to Career Platform API",
        "status": "Healthy",
        "environment": "Development"
    }

@app.get("/test-db")
async def test_database_connection():
    # Asenkron veritabanı motorunu (Engine) burada oluşturuyoruz
    engine = create_async_engine(DATABASE_URL)
    
    try:
        # Veritabanına asenkron olarak ulaşıp ufak bir el sıkışma (ping) yapıyoruz
        async with engine.connect() as connection:
            await connection.execute("SELECT 1")
        return {"status": "Success", "database": "Connected successfully to Docker PostgreSQL!"}
    except Exception as e:
        return {"status": "Error", "details": str(e)}
    finally:
        # Motorun arkada açık kalıp sistemi şişirmemesi için kapatıyoruz
        await engine.dispose()