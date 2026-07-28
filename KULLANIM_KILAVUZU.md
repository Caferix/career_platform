# Dener Makina Kariyer Platformu — Detaylı Kullanım Kılavuzu

Bu doküman, Kariyer Platformu'nun tüm ekranlarının, formlarının ve süreçlerinin nasıl kullanılacağını adım adım açıklar. Kılavuzu okurken sistemde sahip olduğunuz **role (Aday, İnsan Kaynakları, Departman Yöneticisi, Sistem Yöneticisi)** uygun bölümü takip ediniz.

---

## İçindekiler

- [Dener Makina Kariyer Platformu — Detaylı Kullanım Kılavuzu](#dener-makina-kariyer-platformu--detaylı-kullanım-kılavuzu)
  - [İçindekiler](#i̇çindekiler)
  - [Genel Bakış: Kim Nereden Girer?](#genel-bakış-kim-nereden-girer)
  - [BÖLÜM 1 — Aday (Candidate) Kullanım Rehberi](#bölüm-1--aday-candidate-kullanım-rehberi)
    - [1.1. Sisteme Giriş / Kayıt (SMS OTP)](#11-sisteme-giriş--kayıt-sms-otp)
    - [1.2. Profil Bilgilerini Doldurma (`/profile`)](#12-profil-bilgilerini-doldurma-profile)
    - [1.3. Açık İlanları İnceleme ve Başvurma (`/careers`)](#13-açık-i̇lanları-i̇nceleme-ve-başvurma-careers)
    - [1.4. Başvuru Durumunu Takip Etme](#14-başvuru-durumunu-takip-etme)
  - [BÖLÜM 2 — İK / Departman Yöneticisi Paneli (Dashboard)](#bölüm-2--i̇k--departman-yöneticisi-paneli-dashboard)
    - [2.1. Yeni İş İlanı Açma](#21-yeni-i̇ş-i̇lanı-açma)
    - [2.2. Aday Havuzunda Arama ve Filtreleme](#22-aday-havuzunda-arama-ve-filtreleme)
    - [2.3. Aday Detayı, CV İnceleme ve Süreç Güncelleme](#23-aday-detayı-cv-i̇nceleme-ve-süreç-güncelleme)
  - [BÖLÜM 3 — Sistem Yöneticisi (Admin) Paneli](#bölüm-3--sistem-yöneticisi-admin-paneli)
    - [3.1. Şirket Hiyerarşisi: Departman ve Pozisyon Yönetimi](#31-şirket-hiyerarşisi-departman-ve-pozisyon-yönetimi)
    - [3.2. Sistem Kullanıcısı (HR / Manager) Oluşturma ve Yönetimi](#32-sistem-kullanıcısı-hr--manager-oluşturma-ve-yönetimi)
    - [3.3. Sistem Logları ve KVKK Denetimi (Audit)](#33-sistem-logları-ve-kvkk-denetimi-audit)
  - [BÖLÜM 4 — Sık Karşılaşılan Durumlar ve Çözümleri](#bölüm-4--sık-karşılaşılan-durumlar-ve-çözümleri)
  - [BÖLÜM 5 — Güvenlik ve KVKK ile İlgili Kullanıcı Notları](#bölüm-5--güvenlik-ve-kvkk-ile-i̇lgili-kullanıcı-notları)

---

## Genel Bakış: Kim Nereden Girer?

| Kullanıcı Tipi | Giriş Adresi | Kimlik Doğrulama Yöntemi |
|---|---|---|
| Aday | `/login` → "Aday Girişi" sekmesi, ya da doğrudan `/apply` | Telefon numarası + SMS OTP (şifresiz) |
| İnsan Kaynakları (HR) | `/login` → "Yönetici Girişi" sekmesi | Kullanıcı adı + şifre |
| Departman Yöneticisi (Manager) | `/login` → "Yönetici Girişi" sekmesi | Kullanıcı adı + şifre |
| Sistem Yöneticisi (Admin) | `/login` → "Yönetici Girişi" sekmesi, ardından `/admin` paneline geçiş | Kullanıcı adı + şifre |

Herkese açık iş ilanları sayfası (`/careers`) için giriş yapmaya gerek yoktur; ancak bir ilana **başvurmak** için aday olarak giriş yapmış ve profilinizi tamamlamış olmanız gerekir.

---

## BÖLÜM 1 — Aday (Candidate) Kullanım Rehberi

Dışarıdan şirkete başvuran adayların kullanacağı, şifresiz ve SMS doğrulamalı portalin kullanım adımlarıdır.

### 1.1. Sisteme Giriş / Kayıt (SMS OTP)

Sistemde ayrı bir "kayıt ol" formu yoktur — telefon numaranızla ilk kez giriş yaptığınızda hesabınız otomatik oluşur.

1. `/apply` veya `/login` sayfasını açın.
2. **"Aday Girişi"** sekmesinde olduğunuzdan emin olun (Yönetici Girişi yalnızca personel içindir).
3. Başında `0` **olmadan**, 10 haneli güncel cep telefonu numaranızı girin (Örn: `5551234567`).
4. **Giriş Yap / Kayıt Ol** butonuna basın.
5. Telefonunuza 6 haneli tek kullanımlık bir doğrulama kodu gelir.
6. Bu kodu **3 dakika içinde** ekrandaki kutuya girip onaylayın.

> ⏱️ **Kod süresi doldu / gelmedi mi?** Kodun geçerlilik süresi 3 dakikadır. Süre dolduysa "Kodu Tekrar Gönder" ile yeni kod isteyebilirsiniz. Güvenlik amacıyla aynı numaraya **dakikada en fazla 3 kez** kod gönderilebilir; bu limite takılırsanız birkaç dakika bekleyip tekrar deneyin.

### 1.2. Profil Bilgilerini Doldurma (`/profile`)

Giriş yaptıktan sonra sistem sizi **Profilim** sayfasına yönlendirir. Bir ilana başvurabilmek için aşağıdaki alanların (özellikle zorunlu/yıldızlı olanların) eksiksiz doldurulması gerekir.

**Kişisel Bilgiler**
- Ad, Soyad
- Doğum tarihi
- Cinsiyet: *Kadın / Erkek*
- Medeni durum: *Evli / Bekar*
- Uyruk (varsayılan: Türkiye)
- Ehliyet sınıfı (birden fazla seçilebilir)
- Askerlik durumu *(yalnızca erkek adaylar için görünür)*: *Yapıldı / Muaf / Tecilli*

**Adres**
- İl, İlçe (açılır menüden seçilir)
- Açık adres *(bu alan sistemde şifreli saklanır — bkz. [Bölüm 5](#bölüm-5--güvenlik-ve-kvkk-ile-i̇lgili-kullanıcı-notları))*

**Eğitim Bilgileri** — birden fazla eğitim kaydı ekleyebilirsiniz:
- Eğitim seviyesi: *Ortaöğretim / Önlisans / Lisans / Yüksek Lisans / Doktora*
- Okul adı
- Bölüm
- Mezuniyet yılı

**Yabancı Dil Bilgileri** — birden fazla dil ekleyebilirsiniz:
- Dil adı (Örn: İngilizce, Almanca)
- Seviye: CEFR ölçeğine göre A1–C2 arası

**Beceriler ve Deneyim**
- Beceriler: virgülle ayırarak yazın (Örn: `İletişim, AutoCAD, Proje Yönetimi`)
- Sosyal medya / portföy bağlantıları (LinkedIn, GitHub vb. — URL formatında)

**Özgeçmiş (CV) Yükleme**
- Sayfadaki yükleme alanına tıklayarak **PDF** formatındaki özgeçmişinizi seçin.
- Dosya başarıyla yüklendiğinde sistemde onaylı olarak görünür.

**KVKK Onayı**
- Sayfanın altında yer alan Kişisel Verilerin Korunması Kanunu (KVKK) aydınlatma metnini okuyup onay kutucuğunu işaretleyin. Onay verilmeden profil kaydedilemez ve başvuru yapılamaz.

Tüm alanları doldurduktan sonra **Profili Kaydet** butonuna basın.

### 1.3. Açık İlanları İnceleme ve Başvurma (`/careers`)

1. Üst menüden **"İş İlanları"** sayfasına gidin. Burada şirketin o anda aktif olan tüm açık pozisyonları (başlık, departman, lokasyon ve iş tanımı ile birlikte) listelenir.
2. İlgilendiğiniz ilana tıklayarak detayına girin.
3. Profiliniz tamamlanmışsa sayfanın altındaki **"Bu İlana Başvur"** butonuna tıklamanız yeterlidir; ek bir form doldurmanıza gerek yoktur (profilinizdeki bilgiler otomatik kullanılır).
4. Başvuru sırasında isterseniz ilana özel bir **ön yazı (cover letter)**, deneyim özeti ve referans bilgisi ekleyebilirsiniz.

### 1.4. Başvuru Durumunu Takip Etme

**Profilim** sayfasının altındaki **"Başvurularım"** listesinde, yaptığınız her başvurunun güncel durumunu görebilirsiniz:

| Durum | Anlamı |
|---|---|
| Beklemede / Yeni Başvuru | Başvurunuz alınmış, henüz incelenmemiş |
| İncelemede | İK/Manager başvurunuzu değerlendiriyor |
| Kabul Edildi | Süreç olumlu sonuçlanmış |
| Reddedildi | Süreç bu pozisyon için sonlanmış |
| Geri Çekildi | Başvurunuzu siz iptal etmişsiniz |

Bir başvurunuzdan vazgeçmek isterseniz ilgili başvurunun yanındaki **"Başvuruyu Geri Çek"** seçeneğini kullanabilirsiniz.

---

## BÖLÜM 2 — İK / Departman Yöneticisi Paneli (Dashboard)

Şirket içi İnsan Kaynakları (HR) ve Departman Yöneticileri (Manager) tarafından kullanılan aday havuzu ve ilan yönetim panelidir. Giriş, `/login` sayfasındaki **"Yönetici Girişi"** sekmesinden kurumsal kullanıcı adı ve şifre ile yapılır; başarılı girişte `/dashboard` sayfasına yönlendirilirsiniz.

> **⚠️ Rollerin kapsamı (önemli):**
> - **İnsan Kaynakları (HR):** Şirketteki **tüm** departmanları, ilanları ve adayları görebilir; departmanlar arası filtre değiştirebilir.
> - **Departman Yöneticisi (Manager):** Yalnızca yetkilendirildiği **tek departmana** hapsedilmiştir. Örneğin Üretim departmanı yöneticisi sisteme girdiğinde yalnızca Üretim ilanlarını ve bu ilanlara başvuran adayları görür; başka departmanların verilerine erişemez. Bu kısıtlama arka planda sunucu tarafında zorunlu kılınır, yalnızca arayüzde gizlenmiş değildir.

### 2.1. Yeni İş İlanı Açma

1. Dashboard ekranının üstündeki **"Yeni İlan Aç"** butonuna tıklayın.
2. **Departman seçin** (Manager rolündeyseniz bu alan otomatik olarak kendi departmanınıza sabitlenir ve değiştirilemez).
3. **Pozisyon seçin** — departmanı seçtiğiniz anda pozisyon listesi o departmana ait aktif pozisyonlarla dolar (kademeli/cascading seçim).
4. **İlan başlığı** ve **iş tanımını** (görev, aranan nitelikler) yazın.
5. Lokasyon bilgisini girin (Örn: Ofis, Hibrit, Uzaktan).
6. **Kaydet**'e bastığınızda ilan anında `/careers` sayfasında yayına girer.

İlanı daha sonra pasife almak/tekrar aktive etmek için ilan listesindeki **aç/kapat** düğmesini kullanabilirsiniz; ilan verisi hiçbir zaman silinmez (soft delete).

### 2.2. Aday Havuzunda Arama ve Filtreleme

Dashboard'da yüzlerce başvuru listelenebilir. Aradığınızı hızlı bulmak için:

- **Anahtar kelime araması:** İsim, e-posta veya şehir bilgisiyle arayın.
- **Departman / Pozisyon filtresi:** Departman seçtiğinizde pozisyon listesi otomatik daralır.
- **Durum filtresi:** Yalnızca belirli statüdeki başvuruları (Beklemede, İncelemede, Kabul, Ret) görüntüleyin.
- **Deneyim filtresi (min–max yıl):** Örn. "3 ile 5 yıl arası deneyimi olanlar."
- **Tarih aralığı filtresi:** Belirli bir dönemde yapılan başvuruları listeleyin.

Bu filtreler URL sorgu parametreleri (`min_exp`, `max_exp`, `dept_id`, `status`) olarak API'ye iletilir ve sunucu tarafında birleştirilerek uygulanır.

### 2.3. Aday Detayı, CV İnceleme ve Süreç Güncelleme

Listedeki her başvuru satırında:

1. **CV İndir:** Adayın yüklediği PDF özgeçmiş dosyasını indirir veya yeni sekmede açar. *(Bu işlem sistem tarafından loglanır — bkz. Bölüm 3.3.)*
2. **Aday detayını görüntüleme:** Adayın profil bilgilerini (eğitim, dil, iletişim, adres vb.) tam olarak görürsünüz.
3. **Statü güncelleme:** Başvurunun durumunu değiştirin — örneğin incelemeye aldığınızda "İncelemede", süreç bittiğinde "Kabul Edildi" veya "Reddedildi" olarak işaretleyin. Bu değişiklik anında adayın kendi profilindeki başvuru takip ekranına yansır.

---

## BÖLÜM 3 — Sistem Yöneticisi (Admin) Paneli

`/admin` paneli yalnızca **Admin (superadmin)** rolüne sahip kullanıcılara açıktır. Şirketin teknik/organizasyonel kurulumu buradan yapılır.

### 3.1. Şirket Hiyerarşisi: Departman ve Pozisyon Yönetimi

Bu modülden eklenen departman ve pozisyonlar, Dashboard'daki "Yeni İlan Aç" formunu ve `/careers` sayfasındaki filtreleri otomatik besler.

1. **"Şirket Yapısı"** sekmesine girin.
2. **Yeni Departman Ekle** ile ana kategoriyi oluşturun (Örn: Üretim, Yazılım, Satış).
3. **Yeni Pozisyon Ekle** ile ilgili departmanı seçip altına pozisyon ekleyin (Örn: Üretim → "CNC Operatörü").
4. Var olan bir departman veya pozisyonu düzenlemek için satırdaki düzenle (kalem) simgesine tıklayın.

> **Güvenli pasife alma (soft delete):** Bir departmanı veya pozisyonu "silmek" istediğinizde sistem kaydı veritabanından **tamamen kaldırmaz** — yalnızca pasif hale getirir. Böylece o departmana/pozisyona bağlı geçmiş başvurular ve CV'ler bozulmadan saklanır; ancak yeni ilan açma formlarında bu departman/pozisyon artık listelenmez. Pasif bir kaydı istediğiniz zaman tekrar aktive edebilirsiniz.

### 3.2. Sistem Kullanıcısı (HR / Manager) Oluşturma ve Yönetimi

**"Sistem Yöneticileri"** sekmesinden yeni İK uzmanı veya departman yöneticisi hesabı açılır.

- Yeni hesaba **"Manager"** rolü verecekseniz, alttaki departman seçiciden mutlaka bir departman seçmelisiniz — sistem departmansız bir Manager hesabı oluşturulmasına izin vermez.
- **"HR"** rolü verirseniz departman alanı otomatik kilitlenir (HR tüm departmanlara erişebildiği için departman ataması gerekmez).
- Kullanıcı adı ve geçici şifre belirleyip hesabı oluşturun; ilgili kişiye bu bilgileri güvenli bir kanaldan iletin.
- İşten ayrılan veya görevi biten bir yöneticinin erişimini **Etkinleştir / Askıya Al** düğmesiyle anında bloke edebilirsiniz — hesap silinmez, yalnızca pasifleştirilir ve tekrar aktive edilebilir.

### 3.3. Sistem Logları ve KVKK Denetimi (Audit)

Sistemde yapılan tüm hassas işlemler (okuma hariç mutasyonlar ve dosya indirmeler) **"Loglar"** sekmesinde zaman damgasıyla kayıt altına alınır. Örnek log kayıtları:

- `ahmet_hr → Departman pasife alındı: Satış`
- `mehmet_manager → Aday CV'si indirildi: (Aday ID #123)`
- `admin → Yeni sistem kullanıcısı oluşturuldu: (kullanıcı adı)`

Ayrıca **"Başarısız Girişler"** ekranında, yanlış kullanıcı adı/şifre ile yapılan giriş denemeleri IP adresi ve zaman bilgisiyle raporlanır. Olası kaba kuvvet (brute-force) saldırılarını veya iç tehditleri tespit etmek için bu ekranın Admin tarafından düzenli kontrol edilmesi önerilir.

---

## BÖLÜM 4 — Sık Karşılaşılan Durumlar ve Çözümleri

| Durum | Olası Neden | Çözüm |
|---|---|---|
| SMS kodu gelmiyor | Operatör gecikmesi veya yanlış numara girişi | Numarayı kontrol edip "Tekrar Gönder" deneyin; 3 dk sonra kod geçersiz olur |
| "Çok fazla istek" hatası (429) | Kısa sürede birden fazla kod/giriş denemesi yapıldı | Bir dakika bekleyip tekrar deneyin (SMS için 3/dk, admin girişi için 5/dk sınırı vardır) |
| "Bu ilana başvur" butonu pasif | Profil eksik veya KVKK onayı verilmemiş | Profilim sayfasına dönüp zorunlu alanları ve KVKK onayını tamamlayın |
| Manager başka departmanın adaylarını göremiyor | Bu bir hata değil, tasarım gereği | Manager rolü yalnızca kendi departmanına erişebilir; ihtiyaç varsa HR ile iletişime geçin |
| Yeni açılan pozisyon ilan formunda görünmüyor | Departman/pozisyon pasif durumda olabilir | Admin panelinden "Şirket Yapısı" altında ilgili kaydın aktif olduğunu doğrulayın |
| Hesabım "pasif" hatası veriyor | Yönetici hesabınız Admin tarafından askıya alınmış | Sistem yöneticinizle iletişime geçin |

---

## BÖLÜM 5 — Güvenlik ve KVKK ile İlgili Kullanıcı Notları

- Aday girişinde şifre kullanılmaz; kimlik doğrulama yalnızca telefonunuza gelen tek kullanımlık kodla yapılır. Bu kod hiçbir zaman düz metin olarak saklanmaz.
- Profilinizdeki e-posta, telefon ve açık adres bilgileri veritabanında **şifreli** olarak tutulur; yalnızca yetkili sistem bileşenleri tarafından geçici olarak çözülüp görüntülenir.
- CV dosyanız sunucuda rastgele/anlamsız bir dosya adıyla saklanır — dosya adından kimliğinize dair bilgi çıkarılamaz.
- Verilerinize kimlerin ne zaman eriştiği (CV indirme, statü değişikliği vb.) sistem tarafından loglanır ve Admin tarafından denetlenebilir.
- Profilinizi ve KVKK onayınızı istediğiniz zaman güncelleyebilir; hesabınızın silinmesini talep etmek için İK ile iletişime geçebilirsiniz. Silme talebi işlendiğinde kaydınız pasif hale getirilir; kişisel verilerinizin tam anonimleştirilmesi süreci şirketin KVKK prosedürüne göre ayrıca yürütülür.

---

> Sorularınız veya teknik destek talepleriniz için İK departmanınız veya sistem yöneticinizle iletişime geçebilirsiniz.