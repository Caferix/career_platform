import os
from fastapi import FastAPI
from sqlalchemy import text
from app.core.settings import settings
from app.routes.candidates import router as candidate_router
# Veritabanı el sıkışması (ping) testi için engine'i merkezi yerden çekiyoruz
from app.db.database import engine
from app.routes import auth, applications, consents
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routes.applications import router as applications_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.limiter import Limiter, limiter


app = FastAPI(
    title="Career Platform API",
    description="Asenkron, Kriptolu ve Kurumsal Aday Yönetim Sistemi",
    version="1.0.0"
)


#slowapi yi fastapi'ye bağladık
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- ROUTER ENTEGRASYONLARI ---
# Aday (Applicants) endpoint'lerini buraya bağlıyoruz
app.include_router(candidate_router)

#Auth endpointlerini buraya bağlıyoruz
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Başvuru ve CV Yönetimi endpoint'lerini buraya mühürlüyoruz
app.include_router(applications.router)

# KVKK onay endpoint'lerini buraya bağlıyoruz
app.include_router(consents.router)

# 2. CORS Yapılandırması
# Frontend static dosyalar üzerinden geleceği için geliştirme aşamasında tüm kökenlere, 
# metodlara ve header'lara izin veriyoruz.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Static Files Serving (Statik Dosya Sunumu)
# backend/static klasörünün yolunu güvenli bir şekilde çözümlüyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__)) # app/
backend_dir = os.path.dirname(current_dir) # backend/
static_dir_path = os.path.join(backend_dir, "static")

# Eğer klasör yoksa hata vermemesi için otomatik oluşturuyoruz (defansif kodlama)
if not os.path.exists(static_dir_path):
    os.makedirs(static_dir_path)

# /static prefix'i ile static klasörünü dışarı açıyoruz
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- TEMEL ENDPOINT'LER ---
""""""
@app.get("/", tags=["Root"])
async def root():
    """Uygulamanın ayakta olup olmadığını kontrol eden kök dizin."""
    return {
        "message": "Welcome to Career Platform API",
        "status": "Healthy",
        "environment": "Development"
    }
""""""


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
    
# Kolaylık: http://localhost:8000/ adresine girildiğinde direkt index.html'e yönlendirsin veya açsın
@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(static_dir_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>Statik index.html dosyası bulunamadı. Lütfen backend/static/ altında oluşturun.</h3>"    