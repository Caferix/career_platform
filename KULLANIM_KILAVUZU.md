# Dener Makina Kariyer Platformu - Yetkili & Aday Kullanım Kılavuzu

Bu doküman, Kariyer Platformu'nun tüm ekranlarının, formlarının ve süreçlerinin nasıl kullanılacağını detaylı senaryolar eşliğinde adım adım açıklamaktadır. 

Lütfen kılavuzu okurken sistemde sahip olduğunuz **Rol'e (Admin, İnsan Kaynakları, Manager, Aday)** uygun bölümleri dikkate alınız.

---

## BÖLÜM 1: ADAY (CANDIDATE) KULLANIM REHBERİ

Dışarıdan şirketimize başvuran adayların kullanacağı şifresiz, SMS doğrulamalı portalin kullanım adımlarıdır.

### 1.1. Sisteme Kayıt Olma ve OTP Girişi
Sistemde "Şifremi Unuttum" veya "Kayıt Ol" gibi karmaşık formlar yoktur. Kimlik doğrulama telefon numaranızla yapılır.
1. Tarayıcınızdan `http://kariyer.denermakina.com/login` adresine girin.
2. Ekranda ortada bulunan sekmenin **"Aday Girişi"** olduğuna emin olun. (Yönetici Girişi personeller içindir).
3. Ekrana başında "0" *olmadan* 10 haneli güncel telefon numaranızı girin. (Örn: 5551234567).
4. `Giriş Yap / Kayıt Ol` butonuna basın.
5. Telefonunuza **"Dener Kariyer Platformu Giriş Kodunuz: XXXXXX"** şeklinde bir SMS gelecektir.
6. Bu 6 haneli kodu 3 dakika içerisinde ekrandaki kutucuğa girin ve giriş yapın.

### 1.2. KVKK Onayı ve Profil Doldurma (`/profile`)
Giriş yaptıktan sonra sistem sizi otomatik olarak **Profilim** ekranına yönlendirir. Bir iş ilanına başvurabilmeniz için bu ekrandaki tüm yıldızlı (*) alanların dolması şarttır.
*   **Ad / Soyad / Doğum Tarihi / Cinsiyet:** Nüfus cüzdanınızdaki haliyle doldurun.
*   **İl ve İlçe:** Açılır menülerden güncel ikamet adresinizi seçin.
*   **Deneyim Yılı:** Formda bulunan *Deneyim (Yıl)* alanına sektördeki toplam tecrübenizi sayısal olarak girin (Örn: 5). Stajyer veya yeni mezunsanız `0` yazabilirsiniz. İK departmanı adayları incelerken ağırlıklı olarak bu filtreyi kullanır.
*   **Beceriler (Skills):** Uzman olduğunuz alanları virgülle ayırarak yazın (Örn: Python, SolidWorks, C#, Proje Yönetimi).
*   **Özgeçmiş (CV) Yükleme Alanı:** Sayfanın sağ üst köşesindeki alana tıklayarak PDF veya DOCX formatındaki bilgisayarınızdaki özgeçmişinizi yükleyin. Sistem maksimum 5MB'a kadar olan dosyaları kabul etmektedir. Yüklendiğinde yeşil bir "Yüklendi" ikonu belirecektir.
*   **KVKK Onayı:** En altta bulunan Kişisel Verilerin Korunması aydınlatma metnini genişletip okuyun ve "Kabul Ediyorum" kutucuğunu işaretleyin. Bu kutu işaretlenmeden Kaydet butonu aktifleşmez.
*   Mavi renkli `Profili Kaydet` butonuna basarak işlemlerinizi bitirin.

### 1.3. Açık İlanlara Başvurma ve Durum Takibi (`/careers`)
1. Üst menüde yer alan **"İş İlanları"** (Kariyer Fırsatları) sayfasına tıklayın.
2. Dener Makina'nın güncel olarak aradığı tüm açık pozisyonlar (Lokasyon ve İş Tanımları ile birlikte) karşınıza gelecektir.
3. Kendinize uygun ilanı bulduğunuzda `Detayları Gör` diyerek ilanın içine girin.
4. Profiliniz eksiksiz olduğu için en altta yer alan `Bu İlana Başvur` butonuna bir kere tıklamanız yeterlidir. (One-Click Application). Ayrı bir form çıkmayacaktır.
5. **Takip:** Başvurduğunuz işlerin sonucunu öğrenmek için tekrar `Profilim` sayfasına dönün. Sayfanın en altındaki **"Başvurularım"** tablosunda, başvurunuzun şu an `Yeni Başvuru`, `İncelemede` (Mülakat aşaması) veya `Kabul/Ret` durumunda olduğunu şeffaf şekilde görebilirsiniz.

---

## BÖLÜM 2: YÖNETİCİ EKRANLARI (DASHBOARD & HR / MANAGER)

Şirket içi İnsan Kaynakları (HR) ve Departman Yöneticileri (Manager) tarafından kullanılan CV havuzu ve ilan yönetim panelidir. Giriş `http://.../admin` adresindeki "Yönetici Girişi" kısmından kurumsal e-posta ve şifre ile yapılır.

> **⚠️ Rollerin Kapsamı (Çok Önemli):**
> *   **İnsan Kaynakları (HR):** Şirketteki BÜTÜN departmanları, ilanları ve yüzlerce adayı görebilir. Departmanlar arası geçiş yapabilir.
> *   **Departman Yöneticisi (Manager):** Yalnızca yetkilendirildiği departmana hapsedilmiştir. Örneğin "Yazılım Müdürü" sisteme girdiğinde sadece Yazılım ilanlarını ve bu ilanlara başvuran adayları görür. Satış departmanının adaylarına teknik olarak erişemez.

### 2.1. Yeni Kariyer İlanı Açma
1. Sisteme girdiğinizde karşınıza çıkan **Dashboard** ekranının sağ üst köşesindeki `Yeni İlan Aç` butonuna tıklayın. Açılan pencerede (Modal):
2. **Departman Seçimi:** İlanın açılacağı departmanı seçin (Manager'lar bu kutuda sadece kendi departmanlarını görür ve değiştiremezler).
3. **Pozisyon Seçimi:** Departmanı seçtiğiniz anda altındaki Pozisyon kutusu dinamik (cascading) olarak o departmana ait pozisyonlarla (Örn: Kıdemli Geliştirici, Stajyer) dolar. İlgili pozisyonu seçin.
4. **İlan Başlığı:** Adayların siteye girdiğinde göreceği büyük başlıktır.
5. **İş Tanımı ve Kriterler:** Adaylardan beklenen nitelikleri ve işin tanımını yazın.
6. `Kaydet` butonuna basıldığı an ilan web sitesinde "İş İlanları" sekmesinde yayına girer.

### 2.2. Aday Havuzunda Arama ve Gelişmiş Filtreleme
Dashboard ekranında yüzlerce aday listelenebilir. Aradığınız kişiyi bulmak için filtreleme araçlarını kullanın:
*   **Anahtar Kelime Araması:** Hızlı arama kutusuna adayın ismini, e-postasını veya şehrini yazarak filtreleyebilirsiniz.
*   **Kademeli Departman/Pozisyon Filtresi:** "Departman" filtresinden örneğin "Pazarlama"yı seçerseniz, hemen yanındaki "Pozisyon" menüsündeki diğer departmanların pozisyonları kaybolur ve sadece Pazarlama'nın altındaki roller kalır. Böylece çok hızlı daraltma yaparsınız.
*   **Gelişmiş Filtreler (Advanced Filters):** Ekranın sağ üstündeki aşağı ok işaretine (`▾`) tıklayın.
    *   `Deneyim (Min - Max Yıl)`: "Sadece 3 ile 5 yıl arası deneyimi olanları getir."
    *   `Başvuru Tarih Aralığı`: "Sadece geçen hafta başvuranları getir."
    *   Bu filtreler, aday sayısını anında azaltarak hedefe odaklanmanızı sağlar.

### 2.3. Aday CV İnceleme ve Süreç Güncelleme
Tabloda listelenen adayların detaylarını sağdaki butonlardan yönetirsiniz:
1.  **CV İndir:** Mavi butona tıkladığınızda adayın kayıt olurken sisteme yüklediği asıl özgeçmiş dosyası (PDF/DOCX) bilgisayarınıza iner veya yeni sekmede açılır.
2.  **Statü Güncelleme (Action):** İncelediğiniz aday eğer pozisyon için uygunsa, sağ kısımdaki durum menüsünden statüsünü `Under_Review` (İncelemeye Alındı / Mülakat) aşamasına çekin. Süreç sonuçlandığında `Accepted` (Kabul) veya `Rejected` (Red) olarak işaretleyin. Bu durum anlık olarak adayın profiline yansır.

---

## BÖLÜM 3: SİSTEM YÖNETİCİSİ (ADMIN) VE KONFİGÜRASYON

Sadece "Admin" rolüne sahip kişilerin görebildiği özel sekmedir. Şirketin teknik kurulumu buradan yapılır.

### 3.1. Şirket Hiyerarşisi (Departman ve Pozisyon Yönetimi)
Bu modülden eklenen departman ve pozisyonlar, Dashboard'daki ilan açma formunu otomatik olarak besler.
*   `Şirket Yapısı` sekmesine tıklayın.
*   Sol taraftaki "Yeni Departman Ekle" kısmından ana kategorileri oluşturun. Ardından sağ taraftaki "Yeni Pozisyon Ekle" formundan, ilgili departmanı seçerek (Örn: Üretim -> "CNC Operatörü") ağacı genişletin.
*   **Güvenli Pasife Alma (Soft-Delete):** Bir departmanı silmek isterseniz yanındaki turuncu **"Askıya Al / Pasif"** butonuna basın. Sistem bu departmanı veritabanından YOK ETMEZ. Geçmişte bu departmana başvuran binlerce adayın CV verisi sağlam kalır. Ancak bu departman "Gri ve üstü çizili" hale gelir ve İK yeni bir ilan açmak istediğinde artık menülerde bu departmanı göremez.

### 3.2. Yönetici Atama ve Kullanıcı Açma
Sisteme yeni girecek bir İK uzmanı veya Müdür için `Sistem Yöneticileri` sekmesinden hesap açılır.
*   Açılan hesaba **"Manager"** (Departman Yöneticisi) yetkisi verecekseniz, alttaki "Departman" seçici kutusundan mutlaka bir departman (Örn: Finans) seçmek **zorundasınız**. Sistem departmansız bir yönetici eklemenize izin vermez.
*   Hesaba **"HR"** yetkisi verirseniz, departman kutusu kilitlenir ve otomatik olarak "İnsan Kaynakları" atanır.
*   Görevi biten veya işten ayrılan yöneticinin sağ tarafındaki yeşil `Etkinleştir / Askıya Al` butonuna basarak sisteme (Dashboard vb.) erişimini derhal bloke edebilirsiniz.

### 3.3. Sistem Logları ve KVKK Denetimi (Audit)
Sistemde yapılan "okuma" (Read) haricindeki tüm işlemler ve dosya indirmeler `Loglar` sekmesinde saniyesi saniyesine kaydedilir.
*   `Yetkili: ahmet_hr -> Departman Askıya Alındı: Satış`
*   `Yetkili: mehmet_manager -> Aday CV İndirildi: Ali Yılmaz`
*   Ayrıca hatalı / art arda yanlış girilen şifre denemeleri de "Başarısız Girişler" ekranında IP adresi bazlı raporlanmaktadır. Olası siber saldırı veya iç tehdit analizleri için bu ekran Admin tarafından düzenli kontrol edilmelidir.
