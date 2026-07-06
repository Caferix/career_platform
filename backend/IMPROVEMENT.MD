# İyileştirme Notları

Bu dosya, projenin çalışır hale geldikten sonra
uygulanabilecek teknik iyileştirmeleri içerir.

---

## Mimari

### SMS Servis Katmanı — Class Hiyerarşisi
**Dosya:** `app/services/sms.py`  
**Şu an:** Tek fonksiyon `send_sms()`  
**İyileştirme:** SMSProvider base class + TwilioProvider / NetGSMProvider  
**Neden:** Dependency inversion principle, çoklu sağlayıcı desteği  
**Etki:** Route'lar etkilenmez  

---

## Güvenlik

---

## Performans

---

## KVKK / Hukuki

### Soft Delete → Anonimleştirme
**Dosya:** `app/services/candidate.py`  
**Şu an:** Soft delete — is_deleted=True, deleted_at set ediliyor  
**İyileştirme:** Silme talebinde kişisel veriler anonimleştirilerek saklanmalı  
- first_name, last_name → "***"  
- email, phone → rastgele hash  
- cv_url → dosya fiziksel olarak silinmeli  
- Kayıt veritabanında kalır (başvuru istatistikleri bozulmasın)  
- 30 gün sonra hard delete job ile tamamen kaldırılır  
**Neden:** KVKK Madde 7 — kişisel veri silinmeli ama iş verisi korunabilir  
**Etki:** delete_candidate() fonksiyonu güncellenir, başka yer etkilenmez



## DİĞER

### HR ve Departman Yöneticisi Auth Yöntemi

HR ve yönetici auth: email + şifre ile giriş.
users tablosu gerekecek: email, hashed_password, role, department.
POST /auth/login endpoint'i Faz 6'da eklenecek.
Şifre bcrypt ile hash'lenecek — passlib kütüphanesi.

### Twilio Async — SMS Servisi
**Dosya:** `app/services/sms.py`  
**Şu an:** Twilio senkron çalışıyor, async sistemi bloklayabilir  
**İyileştirme:** asyncio.run_in_executor ile thread'e taşı  
veya httpx ile direkt async HTTP isteği  
**Etki:** Sadece sms.py değişir


## CV Yükleme

### CV Versiyon Geçmişi
**Dosya:** `app/services/application.py`, `app/services/storage.py`
**Şu an:** Yeni CV yüklenince eski silinir, üzerine yazılır
**İyileştirme:** Her CV yüklemesinde eski versiyon saklanabilir.
İK hangi CV'yi gördüğünü takip edebilir.
Bunun için `cv_versions` tablosu eklenebilir:
- application_id, cv_url, uploaded_at, is_current
**Etki:** storage.py ve application.py güncellenir

### Dosya Depolama Backend
**Dosya:** `app/services/storage.py`
**Şu an:** Dosyalar local diske kaydediliyor (backend/uploads/)
**İyileştirme:** MinIO veya AWS S3'e taşınabilir.
save_file(), get_file_url(), delete_file() arayüzü sabit kalır,
sadece içi değişir.
**Etki:** Sadece storage.py değişir, route ve servisler etkilenmez

### Dosya I/O — Asenkron Geçiş
**Dosya:** `app/services/storage.py`
**Şu an:** shutil.copyfileobj senkron çalışıyor
**İyileştirme:** aiofiles kütüphanesi ile async I/O
**Etki:** Sadece storage.py değişir