from fastapi import FastAPI
from sqlalchemy import text
from app.core.settings import settings
from app.routes.candidates import router as candidate_router
# Veritabanı el sıkışması (ping) testi için engine'i merkezi yerden çekiyoruz
from app.db.database import engine

app = FastAPI(
    title="Career Platform API",
    description="Asenkron, Kriptolu ve Kurumsal Aday Yönetim Sistemi",
    version="1.0.0"
)

# --- ROUTER ENTEGRASYONLARI ---
# Aday (Applicants) endpoint'lerini buraya temiz bir kol gibi bağlıyoruz
app.include_router(candidate_router)


# --- TEMEL ENDPOINT'LER ---

@app.get("/", tags=["Root"])
async def root():
    """Uygulamanın ayakta olup olmadığını kontrol eden kök dizin."""
    return {
        "message": "Welcome to Career Platform API",
        "status": "Healthy",
        "environment": "Development"
    }


@app.get("/test-db", tags=["Root"])
async def test_database_connection():
    """
    Kural 7: Kurumsal veritabanı sağlık kontrolü (Health Check).
    """
    try:
        async with engine.connect() as connection:
            # <-- 2. Sorguyu text() fonksiyonu içine alıyoruz
            await connection.execute(text("SELECT 1"))
            
        return {
            "status": "Success", 
            "database": "Connected successfully to Docker PostgreSQL!"
        }
    except Exception as e:
        # Hatanın gerçek sebebini terminalde veya debug aşamasında görmek için loglayabilirsin
        return {
            "status": "Error", 
            "details": "Veritabanı bağlantısı başarısız oldu veya sorgu yorumlanamadı."
        }