import os
from fastapi import FastAPI, Depends
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.settings import settings
from app.db.database import engine, get_db  # get_db eklendi
from app.routes import auth, applications, consents 
from app.routes.candidates import router as candidate_router
from app.routes.admin import router as admin_router  # Yeni admin router'ı
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.security import limiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.routes.public_jobs import router as public_jobs_router
from app.routes.job_postings import router as job_postings_router

# Modellerimizi asenkron select sorgusunda kullanmak için import ediyoruz
from app.models.company import Department, Position  # Source 6'daki modeller

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
app.include_router(consents.router) 
app.include_router(admin_router)
app.include_router(public_jobs_router)
app.include_router(job_postings_router)


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


# --- DİNAMİK ORGANİZASYON ŞEMASI ENDPOINT'İ ---
@app.get("/public/positions")
async def get_public_positions(db: AsyncSession = Depends(get_db)):
    """
    Ön yüzlerin (apply ve dashboard) pozisyon-departman ilişkisini
    veritabanından canlı olarak çekebilmesi için düzleştirilmiş sözlüğü döner.
    """
    # Kural 4: select() ve ilişkili pozisyonları tek seferde çekmek için selectinload kullanımı
    stmt = (
        select(Department)
        .where(Department.is_active == True)
        .options(selectinload(Department.positions))
    )
    result = await db.execute(stmt)
    departments = result.scalars().all()
    
    # Ön yüzün eski yapısını bozmamak için veriyi aynı düzleştirilmiş (flat_map) formatta hazırlıyoruz
    flat_map = {}
    for dept in departments:
        for pos in dept.positions:
            if pos.is_active:
                flat_map[pos.name] = dept.name
            
    return flat_map


@app.get("/departments")
async def get_departments(db: AsyncSession = Depends(get_db)):
    """
    apply.html ve dashboard.html'in beklediği iç içe (nested) formatı döner:
    [{ id, name, is_active, positions: [{ id, name, is_active }, ...] }, ...]
    """
    stmt = (
        select(Department)
        .options(selectinload(Department.positions))
    )
    result = await db.execute(stmt)
    departments = result.scalars().all()

    return [
        {
            "id": dept.id,  # Departman ID'si eklendi
            "name": dept.name,
            "is_active": dept.is_active,
            "positions": [
                {
                    "id": pos.id,  # KESİN ÇÖZÜM: Pozisyon ID'si veritabanından çekilip eklendi!
                    "name": pos.name, 
                    "is_active": pos.is_active
                }
                for pos in dept.positions
            ],
        }
        for dept in departments
    ]