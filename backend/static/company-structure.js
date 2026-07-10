// static/company-structure.js

const COMPANY_STRUCTURE = {
    // 🏢 BEYAZ YAKA DEPARTMANLARI
    "Yazılım ve AR-GE Mühendisliği": [
        "Backend Developer", "Frontend Developer", "Android Developer", "Embedded Systems Engineer", "DevOps Engineer", "Android Intern"
    ],
    "Endüstri ve Süreç Yönetimi": [
        "Üretim Planlama Mühendisi", "Kalite Güvence Uzmanı", "Yalın Üretim Yöneticisi"
    ],
    "Satın Alma ve Lojistik": [
        "Tedarik Zinciri Sorumlusu", "Dış Ticaret Uzmanı", "Depo Operasyon Yöneticisi"
    ],
    "İnsan Kaynakları ve İdari İşler": [
        "İK İş Ortağı (HRBP)", "Bordro ve Özlük İşleri Uzmanı", "İş Sağlığı ve Güvenliği Uzmanı"
    ],
    
    // ⚙️ MAVİ YAKA / SAHA DEPARTMANLARI
    "Fabrika Üretim ve Montaj Hattı": [
        "CNC Torna Operatörü", "Montaj Hattı İşçisi", "Robotik Kaynak Teknisyeni"
    ],
    "Bakım onarım ve Tesis Yönetimi": [
        "Mekanik Bakım Teknisyeni", "Endüstriyel Elektrik Teknisyeni", "Otomasyon Teknikeri"
    ],
    "Lojistik ve Sevkiyat": [
        "Forklift Operatörü", "Sevkiyat Elemanı", "Mal Kabul Görevlisi"
    ]
};

// Pozisyondan departmanı tersine bulan yardımcı fonksiyon (apply.html için)
function getDepartmentByPosition(position) {
    for (const [dept, positions] of Object.entries(COMPANY_STRUCTURE)) {
        if (positions.includes(position)) {
            return dept;
        }
    }
    return "Genel Başvuru";
}

// Tüm pozisyonları alfabetik düz liste olarak veren fonksiyon (apply.html ve dashboard.html için)
function getAllPositionsAlphabetical() {
    return Object.values(COMPANY_STRUCTURE).flat().sort();
}