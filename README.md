# Dener Makina Kariyer Platformu — Core ATS Engine

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Asyncpg-336791.svg)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-6BA81E.svg)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-Vanilla-38B2AC.svg)
![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)

Dener Makina için geliştirilmiş, kurum içi açık pozisyonların yönetilmesini, uçtan uca aday başvurularının toplanmasını ve İK (İnsan Kaynakları) süreçlerinin dijitalleştirilmesini sağlayan tam asenkron, KVKK'ya duyarlı bir **Applicant Tracking System (ATS)** projesidir. Backend tamamen FastAPI üzerinde, arayüz ise API'den veri çeken vanilla JS/Tailwind sayfalarından oluşur.


## İçindekiler

1. [Özellikler](#-1-özellikler)
2. [Mimari Tasarım](#-2-mimari-tasarım-architecture-design)
3. [Veritabanı Şeması ve Modeller](#-3-veritabanı-şeması-ve-modeller-database-schema)
4. [Güvenlik ve Kimlik Doğrulama](#-4-güvenlik-ve-kimlik-doğrulama-security-deep-dive)
5. [API Referansı](#-5-api-referansı-endpoints)
6. [Frontend Sayfaları](#-6-frontend-sayfaları)
7. [Kurulum ve Çalıştırma](#-7-kurulum-ve-çalıştırma-adımları)
8. [Ortam Değişkenleri (.env)](#-8-kritik-env-konfigürasyonları)
9. [Docker Mimarisi](#-9-docker-mimarisi-ve-kalıcı-veri-volumes)
10. [Veritabanı Göçleri (Alembic)](#-10-veritabanı-göçleri-alembic)
11. [Geliştirici Kılavuzu](#-11-geliştirici-kılavuzu-yeni-özellik-eklemek)
12. [Bilinen İyileştirme Alanları](#-12-bilinen-i̇yileştirme-alanları)
13. [Proje Durumu ve Katkı](#-13-proje-durumu-ve-katkı)

---

## 🚀 1. Özellikler

- **Şifresiz aday girişi:** Adaylar e-posta/şifre yerine SMS OTP ile sisteme giriş yapar.
- **Çok rollü İK yönetim paneli:** `admin`, `hr`, `manager` rolleriyle departman bazlı yetkilendirme.
- **Dinamik organizasyon şeması:** Departman → Pozisyon → İlan → Başvuru zinciri veritabanından canlı çekilir.
- **Detaylı aday profili:** Kişisel bilgiler, adres, askerlik durumu, çoklu eğitim ve dil kayıtları, sosyal medya bağlantıları.
- **CV yükleme ve güvenli indirme:** PDF'ler UUID ile adlandırılarak diskte saklanır.
- **KVKK uyumluluğu:** Onay (consent) kayıtları, erişim logları (access log), IP/user-agent takibi.
- **Soft delete mimarisi:** Departman, pozisyon, ilan ve aday kayıtları asla kalıcı silinmez.
- **Rate limiting:** SMS ve login uçları brute-force/SMS bombardımanına karşı sınırlandırılmıştır.
- **Başarısız giriş takibi:** `failed_login_attempts` tablosu ile brute-force girişimleri loglanır.

---

## 🏗️ 2. Mimari Tasarım (Architecture Design)

Proje, performans ve eşzamanlı istek kapasitesini maksimize etmek için tamamen **asenkron (non-blocking)** bir altyapı üzerine kurulmuştur. Geleneksel WSGI (Flask/Django) yerine ASGI (FastAPI/Uvicorn) tercih edilmiştir.

### 2.1. Core Tech Stack

| Katman | Teknoloji |
|---|---|
| Web Framework | FastAPI 0.110 (Pydantic v2 entegrasyonlu) |
| Database ORM | SQLAlchemy 2.0 (AsyncSession & `selectinload`) |
| Migration Engine | Alembic |
| Veritabanı | PostgreSQL (asyncpg sürücüsü) |
| Auth & Token | PyJWT, python-jose |
| Şifre Hashleme | Passlib / Bcrypt |
| Rate Limiting | SlowAPI |
| Dış SMS Entegrasyonu | HTTPX (NetGSM), Twilio (alternatif/legacy) |
| Frontend | Vanilla JavaScript, HTML5, TailwindCSS (API'den veri çeken MPA) |

### 2.2. Proje Hiyerarşisi (Directory Structure)

Sistem "Separation of Concerns" (sorumlulukların ayrılığı) prensibiyle tasarlanmıştır:

```text
career_platform/
├── docker-compose.yml       # PostgreSQL konteyneri
├── KULLANIM_KILAVUZU.md     # Son kullanıcı / operasyon kılavuzu
└── backend/
    ├── alembic/              # Veritabanı şema göçleri (migrations)
    │   └── versions/         # 25+ migration dosyası
    ├── api/v1/                # Sürümlenmiş API katmanı (candidates.py)
    ├── app/
    │   ├── core/              # security.py, settings.py, permissions.py
    │   ├── db/                # database.py — async engine & session
    │   ├── models/            # SQLAlchemy tabloları
    │   ├── schemas/           # Pydantic DTO'ları (Create/Update/Response)
    │   ├── services/          # İş mantığı katmanı (business logic)
    │   ├── routes/             # FastAPI endpoint'leri (controller)
    │   └── main.py             # Uygulama giriş noktası & middleware
    ├── static/                # Frontend arayüzleri (HTML/JS/JSON)
    ├── uploads/                # Aday CV'lerinin UUID adlarıyla saklandığı klasör
    ├── seed_users.py           # İlk sistem kullanıcılarını oluşturan script
    ├── IMPROVEMENT.MD          # Teknik borç / iyileştirme notları
    └── requirements.txt        # Bağımlılıklar
```

### 2.3. Katman Sorumlulukları

- **`app/models/`** — Veritabanı tablolarının SQLAlchemy karşılıkları. PII alanları burada property getter/setter ile şeffaf şekilde şifrelenip çözülür.
- **`app/schemas/`** — Pydantic v2 tabanlı giriş/çıkış doğrulama sınıfları. Route'lar asla ham SQLAlchemy nesnesi döndürmez.
- **`app/services/`** — Route'lardan bağımsız iş mantığı (SMS gönderimi, OTP üretimi, dosya depolama, erişim loglama). Route'lar bu servisleri çağırır, iş mantığını kendi içinde barındırmaz.
- **`app/routes/`** — HTTP endpoint tanımları; kimlik doğrulama, yetkilendirme ve servis çağrılarını orkestre eder.
- **`app/core/`** — Uygulama genelinde kullanılan güvenlik yardımcıları (`security.py`: JWT, şifreleme, rate limiter), ayarlar (`settings.py`) ve rol bazlı izin fonksiyonları (`permissions.py`).

---

## 🗄️ 3. Veritabanı Şeması ve Modeller (Database Schema)

PostgreSQL üzerinde tutulan veritabanı, birbirine yabancı anahtarlarla (foreign key) bağlıdır ve SQLAlchemy ORM ile tamamen asenkron nesneler halinde çekilir.

### 3.1. Tablolar

| Model | Tablo | Açıklama |
|---|---|---|
| `User` | `users` | Sistemi kullanan yöneticiler. `role` (admin/hr/manager) ve opsiyonel `department` alanı içerir. |
| `Department` | `departments` | Şirketin organizasyon şeması. `Position` ile bire-çok ilişki. |
| `Position` | `positions` | Departmana bağlı pozisyonlar. |
| `Candidate` | `applicants` | SMS ile kayıt olan dış kullanıcılar (adaylar). Kişisel bilgiler, adres, askerlik, yetenekler. |
| `CandidateEducation` | `candidate_educations` | Adayın birden fazla eğitim kaydı (okul, bölüm, mezuniyet yılı). |
| `CandidateLanguage` | `candidate_languages` | Adayın birden fazla yabancı dil kaydı (dil + CEFR seviyesi). |
| `JobPosting` | `job_postings` | Departman/pozisyona bağlı açık iş ilanları. |
| `Application` | `applications` | Aday ↔ İş İlanı çoka-çok ilişkisini çözen başvuru tablosu. `status` alanı başvurunun aşamasını tutar. |
| `Consent` | `consents` | KVKK onay kayıtları (tip, metin versiyonu, IP, user-agent). |
| `AccessLog` | `access_logs` | Sistemdeki tüm hassas veri erişim/mutasyon işlemlerinin insan-okunur logu. |
| `OTPRecord` | `otp_records` | SMS doğrulama kodlarının hash'lenmiş kayıtları. |
| `FailedLoginAttempt` | `failed_login_attempts` | Başarısız admin/İK giriş denemeleri (brute-force takibi). |

### 3.2. İlişki Diyagramı (özet)

```
Department 1───N Position 1───N JobPosting N───1 User (created_by)
                                     │
                                     N
                                     │
Candidate 1───N Application ────────┘
    │
    ├──N CandidateEducation
    └──N CandidateLanguage
```

### 3.3. Kişisel Verilerin Şifrelenmesi (PII Encryption)

`Candidate` ve `Application` modellerinde e-posta, telefon, açık adres ve referans iletişim bilgisi gibi alanlar veritabanında **Fernet ile şifreli** tutulur (`_email`, `_phone`, `_address_detail`, `_reference_contact` sütunları). Model üzerinde Python `@property` getter/setter kullanılarak bu şifreleme uygulama kodundan tamamen gizlenir — servis katmanı `candidate.email = "..."` yazdığında veri otomatik şifrelenir, okurken otomatik çözülür. Telefon numarası ayrıca aranabilir olması için `hashed_phone` (SHA-256) alanında da tutulur; böylece düz metin telefon numarası hiçbir zaman `WHERE` sorgusunda kullanılmaz.

### 3.4. Soft Delete Algoritması

Projede `Department`, `Position`, `JobPosting` ve `Candidate` kayıtları hiçbir zaman kalıcı silinmez (hard delete yapılmaz). Bunun yerine `is_active = False` ve/veya `is_deleted = True` + `deleted_at` bayrakları atanır. Bu sayede o kayda bağlı geçmiş başvurular veya log kayıtları referential integrity hatası vermeden veritabanında güvenle yaşamaya devam eder. Listeleme uçlarında yalnızca `is_active == True` / `is_deleted == False` olan kayıtlar filtrelenir.

---

## 🛡️ 4. Güvenlik ve Kimlik Doğrulama (Security Deep-Dive)

Sistem iki ayrı kimlik doğrulama akışı kullanır: adaylar için **SMS tabanlı şifresiz doğrulama**, kurumsal kullanıcılar (admin/hr/manager) için **kullanıcı adı + şifre**.

### 4.1. Aday Girişi — OTP Akışı

1. Aday `POST /auth/send-otp` adresine telefon numarasını ve KVKK onayını gönderir.
2. Sistem 6 haneli rastgele bir kod üretir; bunu hash'leyerek `otp_records` tablosuna yazar, son kullanım süresini `OTP_EXPIRY_MINUTES` (varsayılan 3 dakika) ile sınırlar.
3. `app/services/sms.py` içindeki sağlayıcı entegrasyonu (NetGSM/Twilio), `httpx` ile asenkron olarak SMS'i gönderir. `SMS_MOCK_MODE=True` iken gerçek SMS atılmaz, kod loglanır (geliştirme ortamı için).
4. Aday `POST /auth/verify-otp` adresine kodu gönderdiğinde sistem hash doğrulaması yapar ve `Candidate` scope'una sahip bir **JWT** döner.

### 4.2. Kurumsal Kullanıcı Girişi

`POST /auth/login` — login adı + bcrypt hash'lenmiş şifre ile doğrulama yapılır. Başarısız her deneme `failed_login_attempts` tablosuna IP adresiyle birlikte kaydedilir; başarılı girişte rol ve departman bilgisini içeren bir JWT üretilir.

### 4.3. RBAC (Role-Based Access Control)

Roller: `admin` (superadmin), `hr`, `manager`. `app/core/permissions.py` içindeki yardımcı fonksiyonlar yetki kontrolünü merkezileştirir:

```python
def get_department_filter(user: dict):
    # hr/admin: filtre yok (tüm departmanları görür)
    # manager: yalnızca kendi departmanı
    # diğer: erişim yok (False)
    ...

def can_delete_candidate(user: dict) -> bool:
    return user.get("role") == "admin"

def can_manage_users(user: dict) -> bool:
    return user.get("role") == "admin"
```

**Manager izolasyonu:** Manager rolündeki bir kullanıcı dashboard'a eriştiğinde, `app/routes/applications.py` JWT içindeki `department` bilgisini tespit eder ve veritabanı sorgusuna otomatik olarak `WHERE job.department_id = X` filtresi gömer. Manager, istese bile başka departmanların başvurularına/CV'lerine erişemez. `/admin/*` altındaki tüm uçlar ise yalnızca `admin` rolüne (`require_admin` dependency'si ile) açıktır.

### 4.4. Rate Limiting (Brute-Force ve SMS Bombardımanı Koruması)

`SlowAPI` ile hassas uçlar sınırlandırılmıştır:

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 5 istek / dakika |
| `POST /auth/send-otp` | 3 istek / dakika |

Limit aşılırsa `429 Too Many Requests` döner.

### 4.5. Diğer Güvenlik Önlemleri

- Giriş hatalarında "kullanıcı adı veya şifre hatalı" gibi jenerik mesajlar kullanılır (kullanıcı adı sızıntısını önlemek için).
- Pasif (`is_active=False`) kullanıcı hesapları girişte `403 Forbidden` alır.
- CV indirme uçları JWT ile korunur; erişimler `AccessLog` tablosuna yazılır.
- CORS şu an geliştirme kolaylığı için `allow_origins=["*"]` olarak açıktır — **production'a çıkmadan önce belirli origin listesiyle daraltılması önerilir.**

---

## 🔌 5. API Referansı (Endpoints)

Aşağıdaki tablo, `app/routes/` altındaki tüm router'lardan derlenmiştir. Interaktif Swagger dokümantasyonu için sunucu ayaktayken `/docs` adresini ziyaret edin.

### 5.1. Authentication (`/auth`)

| Metod | Yol | Açıklama | Limit |
|---|---|---|---|
| POST | `/auth/login` | Admin/HR/Manager girişi (kullanıcı adı + şifre) | 5/dk |
| POST | `/auth/send-otp` | Adaya SMS doğrulama kodu gönderir | 3/dk |
| POST | `/auth/verify-otp` | OTP kodunu doğrular, aday JWT'si döner | — |

### 5.2. Applicants / Adaylar (`/applicants`)

| Metod | Yol | Açıklama |
|---|---|---|
| GET | `/applicants/me` | Giriş yapmış adayın kendi profilini döner |
| POST | `/applicants/` | Yeni aday profili tamamlar |
| GET | `/applicants/{id}` | ID ile aday getirir |
| GET | `/applicants/` | Tüm adayları listeler (İK) |
| PUT | `/applicants/{id}` | Aday bilgilerini günceller |
| DELETE | `/applicants/{id}` | Adayı soft-delete yapar |
| POST | `/applicants/{id}/educations` | Adaya eğitim kaydı ekler |
| DELETE | `/applicants/educations/{edu_id}` | Eğitim kaydını siler |
| POST | `/applicants/{id}/languages` | Adaya dil kaydı ekler |
| DELETE | `/applicants/languages/{lang_id}` | Dil kaydını siler |

### 5.3. Applications / Başvurular (`/applications`)

| Metod | Yol | Açıklama |
|---|---|---|
| POST | `/applications/` | Yeni başvuru oluşturur |
| POST | `/applications/{id}/upload-cv` | Başvuruya CV (PDF) yükler |
| GET | `/applications/{id}/cv` | CV dosyasını indirir (yetki kontrollü) |
| GET | `/applications/` | Başvuruları listeler — `min_exp`, `max_exp`, `dept_id`, `status` gibi query parametreleriyle dinamik filtreleme yapılır |
| PATCH | `/applications/{id}/status` | Başvuru durumunu günceller (İK/Manager) |
| PATCH | `/applications/{id}/withdraw` | Aday kendi başvurusunu geri çeker |

### 5.4. Job Postings — İç Yönetim (`/job-postings`)

| Metod | Yol | Açıklama |
|---|---|---|
| POST | `/job-postings` | Yeni iş ilanı açar (HR/Manager) |
| GET | `/job-postings` | Departmana göre ilanları listeler |
| PATCH | `/job-postings/{id}` | İlanı günceller |
| POST | `/job-postings/{id}/toggle` | İlanı aktif/pasif yapar |

### 5.5. Public Job Postings (`/public/jobs`)

| Metod | Yol | Açıklama |
|---|---|---|
| GET | `/public/jobs` | Herkese açık, aktif iş ilanları listesi |
| GET | `/public/jobs/{id}` | Herkese açık ilan detayı |

### 5.6. Consents / KVKK Onayları (`/consents`)

| Metod | Yol | Açıklama |
|---|---|---|
| POST | `/consents/` | Yeni KVKK onay kaydı oluşturur (IP + user-agent ile) |

### 5.7. Admin Operations (`/admin`) — yalnızca `admin` rolü

| Metod | Yol | Açıklama |
|---|---|---|
| POST | `/admin/departments` | Yeni departman oluşturur |
| GET | `/admin/departments` | Departmanları listeler |
| PATCH | `/admin/departments/{id}` | Departman günceller |
| DELETE | `/admin/departments/{id}` | Departmanı soft-delete yapar (iki farklı route ile: `id` ve `dept_id`) |
| POST | `/admin/positions` | Yeni pozisyon oluşturur |
| PATCH | `/admin/positions/{id}` | Pozisyon günceller |
| DELETE | `/admin/positions/{id}` | Pozisyonu soft-delete yapar (iki farklı route ile: `id` ve `pos_id`) |
| POST | `/admin/users` | Yeni sistem kullanıcısı (İK/Manager) oluşturur |
| GET | `/admin/users` | Sistem kullanıcılarını listeler |
| POST | `/admin/users/{id}/toggle` | Kullanıcıyı aktif/pasif yapar |
| DELETE | `/admin/candidates/{id}` | Adayı soft-delete yapar |
| GET | `/admin/access-logs` | Erişim/mutasyon loglarını görüntüler |
| GET | `/admin/failed-logins` | Başarısız giriş denemelerini görüntüler |

### 5.8. Kök / Organizasyon Uçları (`main.py`)

| Metod | Yol | Açıklama |
|---|---|---|
| GET | `/test-db` | Veritabanı bağlantı sağlığını test eder |
| GET | `/departments` | Departman + pozisyonları nested (iç içe) JSON olarak döner |
| GET | `/public/positions` | Departman-pozisyon ilişkisini düzleştirilmiş (`{pozisyon: departman}`) sözlük olarak döner |

### 5.9. Servis Katmanı (`app/services/`)

API uçlarının arkasındaki iş mantığı bu katmanda toplanır, böylece kod tekrarı önlenir:

- **`storage.py`** — Yüklenen PDF'lerin uzantısını doğrular, dosya adını UUID4'e çevirir, diske asenkron kaydeder.
- **`access_log.py`** — Sistemde yapılan tüm hassas mutasyonları (kim sildi, kimi pasife aldı, kimin CV'sini indirdi) `AccessLog` tablosuna insan-okunur Türkçe metinlerle yazar.
- **`otp.py` / `sms.py`** — OTP üretimi, hash'lenmesi ve SMS gönderim entegrasyonu.
- **`auth.py`, `user.py`, `candidate.py`, `application.py`, `consent.py`** — İlgili domain'lerin CRUD ve doğrulama mantığı.

---

## 🖥️ 6. Frontend Sayfaları

`backend/static/` altındaki sayfalar, `main.py` içinde tanımlı route'larla sunulur (SPA benzeri MPA mimarisi — her sayfa API'den canlı veri çeker):

| Route | Dosya | Açıklama |
|---|---|---|
| `/` | `index.html` | Ana giriş sayfası |
| `/login` | `login.html` | Kurumsal kullanıcı (admin/hr/manager) girişi |
| `/careers` | `jobs.html` | Herkese açık iş ilanları listesi |
| `/apply` | `apply.html` | Aday başvuru formu (SMS OTP girişli) |
| `/profile` | `profile.html` | Aday profil yönetimi (eğitim, dil, kişisel bilgiler) |
| `/dashboard` | `dashboard.html` | İK/Manager başvuru yönetim paneli |
| `/admin` | `admin.html` | Superadmin yönetim paneli (departman, pozisyon, kullanıcı, log) |

Destekleyici statik dosyalar: `company-structure.js` (organizasyon şeması render mantığı), `countries.json` / `locations.json` (form referans verileri), `kvkk.pdf` (aydınlatma metni).

---

## 🛠️ 7. Kurulum ve Çalıştırma Adımları

Proje hem **Docker Compose** ile tek komutla (veritabanı + backend dâhil) hem de **Yerel Python Ortamında** çalıştırılabilir. Başka bir bilgisayarda en kolay ve sorunsuz çalıştırma yöntemi **Docker Compose** kullanmaktır.

### 7.1. Ön Gereksinimler

- **Docker & Docker Compose** (Herhangi bir bilgisayarda projeyi çalıştırmak için yeterlidir)
- *(Opsiyonel — Yerel geliştirme için)*: **Python 3.12+** ve **PostgreSQL**

---

### 🚀 7.2. Yöntem 1: Docker ile Tek Tıkla Kurulum (Önerilen)

Projeyi başka bir bilgisayarda tamamen sıfırdan çalıştırmak için sırasıyla şu adımları izleyin:

```bash
# 1. Repoyu klonlayın
git clone https://github.com/Caferix/career_platform.git
cd career_platform

# 2. backend/.env.example dosyasını .env olarak kopyalayın
cp backend/.env.example backend/.env

# 3. Docker konteynerlerini (PostgreSQL + FastAPI Web) ayağa kaldırın
docker-compose up -d --build

# 4. Veritabanı şemasını ve tablolarını oluşturun (Alembic Migration)
docker exec -it career_platform_web alembic upgrade head

# 5. İlk sistem kullanıcısını (admin) ve varsayılan verileri oluşturun
docker exec -it career_platform_web python seed_users.py
```

Uygulama başarıyla çalışmaya başladıktan sonra erişim adresleri:
- 🌐 **Ana Uygulama / Arayüz**: `http://localhost:8000/`
- 📄 **Swagger API Dokümantasyonu**: `http://localhost:8000/docs`
- 📄 **ReDoc**: `http://localhost:8000/redoc`

**Docker Yönetim Komutları:**
```bash
# Durdurmak için:
docker-compose stop

# Yeniden başlatmak için:
docker-compose start

# Konteynerleri ve ağı tamamen kaldırmak için:
docker-compose down
```

---

### 💻 7.3. Yöntem 2: Yerel Geliştirici Kurulumu (Local Development)

Sadece veritabanını Docker'da çalıştırıp backend kodunu kendi bilgisayarınızda (hot-reload ile) geliştirmek isterseniz:

```bash
# 1. Repoyu klonlayın ve backend dizinine girin
git clone https://github.com/Caferix/career_platform.git
cd career_platform/backend

# 2. Python sanal ortamı (venv) oluşturun ve aktif edin
python3 -m venv venv
source venv/bin/activate      # Windows için: venv\Scripts\activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. .env dosyasını oluşturun
cp .env.example .env

# 5. Sadece veritabanı konteynerini ayağa kaldırın
cd .. && docker-compose up -d db && cd backend

# 6. .env dosyasında DATABASE_URL adresini db yerine localhost yapın:
# DATABASE_URL=postgresql+asyncpg://career_admin:career_secure_password_2026@localhost:5432/career_platform_prod

# 7. Veritabanı tablolarını ve seed verilerini oluşturun
alembic upgrade head
python seed_users.py

# 8. Uvicorn sunucusunu başlatın
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ⚙️ 8. Kritik .env Konfigürasyonları

Uygulamanın `app/core/settings.py` modülü Pydantic `BaseSettings` kullanır ve aşağıdaki tüm ortam değişkenlerinin `.env` dosyasında eksiksiz bulunmasını bekler. Eksik bir değişken olduğunda uygulama başlatma anında doğrulama hatası (ValidationError) verir.

`.env` dosyasındaki güncel ve gerekli değişken listesi:

```env
# Veritabanı URL'si (Docker Compose için 'db', yerel çalıştırma için 'localhost')
DATABASE_URL=postgresql+asyncpg://career_admin:career_secure_password_2026@db:5432/career_platform_prod

# JWT Güvenlik Ayarları
JWT_SECRET_KEY=498d36c9743438a0a2db044a909eb83b52a3a061b5070f49cb44e76d2e6a65d6
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# Kişisel Veri Şifreleme Anahtarı (Fernet - PII Encryption Key)
ENCRYPTION_KEY=a5DtZUEbxQiWe1y3oKA362XurfRBRPF8-qoUqTRhoD0=

# SMS Entegrasyonu (NetGSM / Mock Mode)
NETGSM_USER=mock_user
NETGSM_PASSWORD=mock_password
NETGSM_HEADER=mock_header
SMS_MOCK_MODE=True
OTP_EXPIRY_MINUTES=3

# Uygulama Temel URL
BASE_URL=http://localhost:8000

# İlk Yönetici Giriş Bilgileri (seed_users.py tarafından oluşturulur)
ADMIN_LOGIN=admin
ADMIN_PASSWORD=AdminSecurePass123!
```

> ⚠️ **Güvenlik Notu:** Production ortamına canlıya alınırken `JWT_SECRET_KEY` ve `ENCRYPTION_KEY` değerleri rastgele ve güçlü karakter dizileriyle yenilenmelidir.

---

## 🐳 9. Docker Mimarisi ve Kalıcı Veri (Volumes)

Projede hem veritabanı hem de FastAPI backend servisi Docker konteynerleri olarak yapılandırılmıştır (`docker-compose.yml`).

### Kalıcı Veri Depolama (Volumes)
Sistemde veri kaybını önlemek için iki adet Docker hacmi (volume) kullanılır:
1. **`postgres_data`**: Veritabanı tablolarının ve verilerinin konteyner silinse bile kalıcı olarak kalmasını sağlar.
2. **`backend_uploads`**: Adaylar tarafından sisteme yüklenen özgeçmiş (CV PDF) dosyalarının diskte kalıcı saklandığı dizindir.

---

## 🧬 10. Veritabanı Göçleri (Alembic)

Proje 25'in üzerinde migration dosyasıyla organik olarak büyümüştür (aday profil alanları, eğitim/dil tabloları, consent & access log tabloları, iş ilanı sistemi, brute-force takip tablosu vb. adım adım eklenmiştir).

```bash
# Yeni bir migration oluştur (modellerdeki değişikliği otomatik algılar)
alembic revision --autogenerate -m "aciklayici_mesaj"

# Migration'ları veritabanına uygula
alembic upgrade head

# Bir migration geri al
alembic downgrade -1

# Migration geçmişini görüntüle
alembic history
```

---

## 🧪 11. Geliştirici Kılavuzu: Yeni Özellik Eklemek

Sisteme yeni bir tablo veya API eklemek için standart iş akışı:

1. **Model:** `app/models/` içine yeni sınıfınızı `Base`'den türeterek yazın.
2. **Migration:** `alembic revision --autogenerate -m "yeni_tablo"` ile migration oluşturun, ardından `alembic upgrade head` ile uygulayın.
3. **Schema:** `app/schemas/` altında Pydantic doğrulama sınıflarını (`Create`, `Update`, `Response`) yazın. ORM desteği için `model_config = {"from_attributes": True}` eklemeyi unutmayın.
4. **Service:** İş mantığını `app/services/` altında ayrı bir fonksiyon/modül olarak yazın — route'lar yalnızca orkestrasyon yapmalı.
5. **Route:** `app/routes/` altında endpoint'i tanımlayın ve `main.py` içine `app.include_router()` ile kaydedin.
6. **Yetkilendirme:** Gerekiyorsa `app/core/permissions.py` içine yeni bir izin fonksiyonu ekleyin ve route'ta `Depends()` ile kullanın.

---

## 📋 12. Bilinen İyileştirme Alanları

`backend/IMPROVEMENT.MD` dosyasında detaylandırılan, bilinçli olarak ertelenmiş teknik borçlar:

- **SMS servis katmanı:** Şu an tek fonksiyon (`send_sms()`); `SMSProvider` base class + `TwilioProvider`/`NetGSMProvider` alt sınıflarıyla dependency inversion uygulanması planlanıyor.
- **KVKK silme talepleri:** Şu an soft delete (`is_deleted=True`) yapılıyor; ileride kişisel verilerin anonimleştirilmesi (ad/soyad/telefon/e-posta maskeleme, CV dosyasının fiziksel silinmesi) ve 30 gün sonrasında hard-delete job'ı eklenmesi hedefleniyor.
- **CORS:** Geliştirme kolaylığı için `allow_origins=["*"]` açık; production'a geçişte belirli origin'lerle sınırlandırılmalı.

---

## 📌 13. Proje Durumu ve Katkı

Bu proje, staj kapsamında **Cafer Ceviz** tarafından modern yazılım mühendisliği prensipleri (asenkron I/O, gevşek bağlılık/loose coupling, RBAC, veri doğrulama, KVKK farkındalığı) gözetilerek sıfırdan kodlanmıştır. Aktif geliştirme aşamasındadır; kurumsal genişlemelere ve modüler yapıya tamamen açıktır.

**İletişim:** cafer.ceviz.dev@gmail.com