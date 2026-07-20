import os
from fastapi import FastAPI
from sqlalchemy import text
from app.core.settings import settings
from app.routes.candidates import router as candidate_router
from app.db.database import engine
# 🌟 DÜZELTME 1: consents router'ını import listesine dahil ediyoruz
from app.routes import auth, applications, consents 
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.security import limiter
from app.routes.applications import router as applications_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse


app = FastAPI(
    title="Career Platform API",
    description="Asenkron, Kriptolu ve Kurumsal Aday Yönetim Sistemi",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- ROUTER ENTEGRASYONLARI ---
app.include_router(candidate_router)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(applications.router)
# 🌟 DÜZELTME 2: consents rotasını ana uygulamaya tamamen mühürlüyoruz!
app.include_router(consents.router) 

# 2. CORS Yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Static Files Serving (Statik Dosya Sunumu)
current_dir = os.path.dirname(os.path.abspath(__file__)) 
backend_dir = os.path.dirname(current_dir) 
static_dir_path = os.path.join(backend_dir, "static")

if not os.path.exists(static_dir_path):
    os.makedirs(static_dir_path)

app.mount("/static", StaticFiles(directory="static"), name="static")


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
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            
        return {
            "status": "Success", 
            "database": "Connected successfully to Docker PostgreSQL!"
        }
    except Exception as e:
        return {
            "status": "Error", 
            "details": "Veritabanı bağlantısı başarısız oldu veya sorgu yorumlanamadı."
        }
    
@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(static_dir_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>Statik index.html dosyası bulunamadı. Lütfen backend/static/ altında oluşturun.</h3>"


    # app/main.py dosyasının en altına ekle:

@app.get("/public/positions")
async def get_public_positions():
    """
    Ön yüzlerin (apply ve dashboard) pozisyon-departman ilişkisini
    canlı olarak çekebilmesi için merkezi sözlüğü döner.
    """
    # Şirket/Platform organizasyon şemasının merkezi burasıdır.
    # İleride veritabanına taşınacak olan yapı tam olarak budur.
    structure = {
        "Yazılım Geliştirme": [
            "Backend Developer", 
            "Frontend Developer", 
            "Android Developer", 
            "iOS Developer",
            "DevOps Engineer",
            "Android Intern"
        ],
        "Gömülü Sistemler": [
            "Embedded Systems Engineer",
            "Embedded Intern"
        ],
        "Siber Güvenlik": [
            "Cybersecurity Expert", 
            "Penetration Tester"
        ],
        "İnsan Kaynakları": [
            "HR Intern", 
            "Talent Acquisition Specialist"
        ]
    }
    
    # Ön yüzün kolayca "Pozisyon -> Departman" araması yapabilmesi için yapıyı düzleştiriyoruz
    flat_map = {}
    for dept, positions in structure.items():
        for pos in positions:
            flat_map[pos] = dept
            
    return flat_map