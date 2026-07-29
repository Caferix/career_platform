from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.candidate import Candidate, CandidateEducation, CandidateLanguage
from app.models.consents import Consent
from app.schemas.candidate import CandidateCreate, CandidateUpdate, EducationSchema, LanguageSchema
from app.core.security import hash_data
from app.models.candidate import Application

async def create_candidate(
    db: AsyncSession, 
    data: CandidateCreate, 
    ip_address: str,
    user_agent: str = None,
    is_communication_consented: bool = False
) -> Candidate:
    """
    Deterministik SHA-256 hash'i (hashed_phone) üzerinden mükerrer kontrolü yapar,
    veriyi property'ler aracılığıyla şifreler, alt tabloları ve rızaları atomic olarak kaydeder.
    """
    # 1. ADIM: Telefonun deterministik hash'ini üretiyoruz
    phone_search_hash = hash_data(data.phone)
    
    # 2. ADIM: Aramayı şifreli alanda değil, deterministik hash sütununda yapıyoruz
    query = select(Candidate).where(
        Candidate.hashed_phone == phone_search_hash,
        Candidate.is_deleted == False
    )
    result = await db.execute(query)
    existing = result.scalars().first()
    
    if existing:
        # Veri sızıntısını (User Enumeration) önlemek için jenerik hata
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Girilen bilgilerle daha önce işlem yapılmıştır. Lütfen kontrol edip tekrar deneyiniz."
        )
    
    try:
        # 3. ADIM: Nesneyi temizlenmiş düz verilerle besliyoruz (Setter'lar otomatik şifreleyecek)
        candidate = Candidate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,               
            phone=data.phone,               
            hashed_phone=phone_search_hash, # WHERE aramaları için indeksli alan
            birth_date=data.birth_date,
            nationality=data.nationality,
            marital_status=data.marital_status,
            driving_license=data.driving_license,
            gender=data.gender,
            city=data.city,
            district=data.district,
            address_detail=data.address_detail, 
            military_status=data.military_status,
            skills=data.skills,
            social_link=data.social_links,
            is_phone_verified=True
        )
        
        db.add(candidate)
        await db.flush()  # Alt tablolar için ID'yi ürettirip transaction'ı açık tutuyoruz
        
        # 4. ADIM: Çoklu Eğitim Geçmişi (Alt Tablo)
        if data.educations:
            for edu in data.educations:
                new_edu = CandidateEducation(
                    applicant_id=candidate.id,
                    education_level=edu.education_level,
                    school_name=edu.school_name,
                    department=edu.department,
                    graduation_year=edu.graduation_year
                )
                db.add(new_edu)
            
        # 5. ADIM: Çoklu Yabancı Dil Bilgisi (Alt Tablo)
        if data.languages:
            for lang in data.languages:
                new_lang = CandidateLanguage(
                    applicant_id=candidate.id,
                    language_name=lang.language_name,
                    level=lang.level
                )
                db.add(new_lang)

        # 6. ADIM: Hukuki Onaylar (Consents) - Sadece IP adresi ile
        kvkk_consent = Consent(
            applicant_id=candidate.id,
            consent_type="kvkk",
            consent_text_version="v2026.1",
            ip_address=ip_address,
            user_agent = user_agent,
            is_active=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(kvkk_consent)
        
        if is_communication_consented:
            comm_consent = Consent(
                applicant_id=candidate.id,
                consent_type="communication",
                consent_text_version="v2026.1",
                ip_address=ip_address,
                user_agent = user_agent,
                is_active=True,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            db.add(comm_consent)

        # 7. ADIM: DB Mühürleme
        await db.commit()
        await db.refresh(candidate)
        return candidate

    except Exception:
        await db.rollback()
        # Hata detayı gizlendi
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Aday profil kaydı esnasında sistem hatası oluştu."
        )

async def get_candidate(db: AsyncSession, candidate_id: int):
    """
    Belirtilen ID'ye sahip adayı, ilişkili alt tablolarıyla birlikte (selectinload)
    asenkron uyumlu olarak veritabanından çeker.
    """
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == candidate_id, Candidate.is_deleted == False)
        .options(
            selectinload(Candidate.applications),
            selectinload(Candidate.educations),
            selectinload(Candidate.languages)
        )
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Aday bulunamadı.")
        
    return candidate

async def list_candidates(db: AsyncSession, skip: int = 0, limit: int = 10, current_user: dict = None) -> list[Candidate]:
    """
    Aktif adayları yetki ve departman sınırlarına göre filtreleyerek asenkron listeler.
    - Admin/HR: Tüm aday havuzunu görebilir.
    - Manager: Sadece kendi departmanındaki pozisyonlara başvurmuş adayları görebilir.
    """
    # 1. Temel sorgumuzu aktif adaylar için oluşturuyoruz
    query = select(Candidate).where(Candidate.is_deleted == False)

    if current_user:
        user_role = current_user.get("role")
        user_dept = current_user.get("department")

        # Güvenlik Kontrolü: Dış adaylar genel havuzu listeleyemez
        if user_role == "applicant":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Bu işlem için yetkiniz bulunmamaktadır."
            )

        # Manager Filtresi: Sadece kendi departmanının başvurularını içeren adayları SQL seviyesinde kısıtla
        if user_role == "manager":
            if not user_dept:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Yönetici departman bilgisi eksik."
                )
            
            # İlişkisel join ve distinct filtrelemesi uyguluyoruz
            query = (
                query.join(Candidate.applications)
                .where(Application.department == user_dept)
                .distinct()
            )

    # 2. Sayfalama uygulayıp asenkron olarak veritabanından çekiyoruz
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_candidate(db: AsyncSession, candidate_id: int, data: CandidateUpdate) -> Candidate:
    """Adayı asenkron şifreleme kurallarına (Property Setter) göre günceller."""
    candidate = await get_candidate(db, candidate_id)
    update_dict = data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        if key == "phone":
            # Setter property otomatik şifreleyecek, biz sadece hash'i ayrıca güncelliyoruz
            candidate.phone = value 
            candidate.hashed_phone = hash_data(value)
        else:
            # Email, address_detail vb. gelirse de kendi setter'ları devreye girecek
            setattr(candidate, key, value)
            
    candidate.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(candidate)
    return candidate

async def delete_candidate(db: AsyncSession, candidate_id: int) -> None:
    """Yumuşak silme (Soft Delete) operasyonu."""
    candidate = await get_candidate(db, candidate_id)
    candidate.is_deleted = True
    candidate.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()


# --- EĞİTİM: EKLEME / SİLME ---

async def add_education(db: AsyncSession, candidate_id: int, data: EducationSchema) -> CandidateEducation:
    """Var olan bir adaya tek bir eğitim kaydı ekler."""
    # Adayın gerçekten var (ve silinmemiş) olduğunu doğrula
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.is_deleted == False)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aday bulunamadı.")

    new_edu = CandidateEducation(
        applicant_id=candidate_id,
        education_level=data.education_level,
        school_name=data.school_name,
        department=data.department,
        graduation_year=data.graduation_year
    )
    db.add(new_edu)
    await db.commit()
    await db.refresh(new_edu)
    return new_edu


async def delete_education(db: AsyncSession, edu_id: int) -> None:
    """Belirtilen eğitim kaydını kalıcı olarak siler (hard delete)."""
    result = await db.execute(
        select(CandidateEducation).where(CandidateEducation.id == edu_id)
    )
    edu_record = result.scalar_one_or_none()

    if not edu_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eğitim kaydı bulunamadı.")

    await db.delete(edu_record)
    await db.commit()


# --- DİL: EKLEME / SİLME ---

async def add_language(db: AsyncSession, candidate_id: int, data: LanguageSchema) -> CandidateLanguage:
    """Var olan bir adaya tek bir yabancı dil kaydı ekler."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.is_deleted == False)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aday bulunamadı.")

    new_lang = CandidateLanguage(
        applicant_id=candidate_id,
        language_name=data.language_name,
        level=data.level
    )
    db.add(new_lang)
    await db.commit()
    await db.refresh(new_lang)
    return new_lang


async def delete_language(db: AsyncSession, lang_id: int) -> None:
    """Belirtilen dil kaydını kalıcı olarak siler (hard delete)."""
    result = await db.execute(
        select(CandidateLanguage).where(CandidateLanguage.id == lang_id)
    )
    lang_record = result.scalar_one_or_none()

    if not lang_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dil kaydı bulunamadı.")

    await db.delete(lang_record)
    await db.commit()


async def get_or_create_shadow_candidate(
    db: AsyncSession, 
    phone: str, 
    ip_address: str, 
    user_agent: str
) -> int:
    """
    Telefon numarasına ait aday varsa doğrudan ID'sini döner.
    Yoksa sadece telefonla 'Gölge Aday' oluşturur ve 'phone_verification' rızasını mühürler.
    """
    # 1. Hash fonksiyonunu tek merkezden çağırıyoruz
    phone_search_hash = hash_data(phone)
    
    # 2. Aktif adayı sorguluyoruz
    query = select(Candidate).where(
        Candidate.hashed_phone == phone_search_hash,
        Candidate.is_deleted == False
    )
    result = await db.execute(query)
    candidate = result.scalars().first()
    
    if candidate:
        # Aday zaten varsa (ve silinmemişse) mevcut ID'sini dönüyoruz
        return candidate.id

    try:
        # 3. Yoksa sadece telefonla "Gölge Aday" kaydı açıyoruz
        shadow_candidate = Candidate(
            phone=phone,
            hashed_phone=phone_search_hash,
            is_phone_verified=True
        )
        db.add(shadow_candidate)
        await db.flush()  # ID üretmek için flush yapıyoruz
        
        # 4. phone_verification rızasını mühürlüyoruz
        phone_consent = Consent(
            applicant_id=shadow_candidate.id,
            consent_type="phone_verification",
            consent_text_version="v2026.1",
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)  # naive datetime korundu
        )
        db.add(phone_consent)
        await db.commit()
        
        return shadow_candidate.id

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gölge aday kaydı esnasında sistem hatası oluştu."
        )
    

async def complete_shadow_candidate(
    db: AsyncSession,
    candidate_id: int,
    data: CandidateCreate,
    ip_address: str,
    user_agent: str = None,
    is_communication_consented: bool = False
) -> Candidate:
    """
    Önceden oluşturulmuş gölge adayın boş kişisel alanlarını tamamlar (giydirir),
    dinamik alt tablolarını (eğitim/dil) ekler ve kalan yasal rızaları mühürler.
    """
    # 1. Mevcut aktif gölge adayı ID üzerinden çekiyoruz
    candidate = await get_candidate(db, candidate_id)

    try:
        # 2. Temel profil bilgilerini gölge adaya giydiriyoruz
        candidate.first_name = data.first_name
        candidate.last_name = data.last_name
        candidate.email = data.email  # Setter property otomatik şifreleyecek
        candidate.birth_date = data.birth_date
        candidate.nationality = data.nationality
        candidate.marital_status = data.marital_status
        candidate.driving_license = data.driving_license
        candidate.gender = data.gender
        candidate.social_links = data.social_links
        candidate.city = data.city
        candidate.district = data.district
        candidate.address_detail = data.address_detail  # Setter property otomatik şifreleyecek
        candidate.military_status = data.military_status
        candidate.skills = data.skills
       
        
        # 3. Çoklu Eğitim Geçmişini bağlıyoruz (Alt Tablo)
        if data.educations:
            for edu in data.educations:
                new_edu = CandidateEducation(
                    applicant_id=candidate.id,
                    education_level=edu.education_level,
                    school_name=edu.school_name,
                    department=edu.department,
                    graduation_year=edu.graduation_year
                )
                db.add(new_edu)

        # 4. Çoklu Dil Bilgisini bağlıyoruz (Alt Tablo)
        if data.languages:
            for lang in data.languages:
                new_lang = CandidateLanguage(
                    applicant_id=candidate.id,
                    language_name=lang.language_name,
                    level=lang.level
                )
                db.add(new_lang)

        # 5. Yasal Rızalar: KVKK Aydınlatma Metni Onayı
        kvkk_consent = Consent(
            applicant_id=candidate.id,
            consent_type="kvkk",
            consent_text_version="v2026.1",
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) # naive datetime
        )
        db.add(kvkk_consent)

        # 6. Yasal Rızalar: Opsiyonel Pazarlama/İletişim Onayı
        if is_communication_consented:
            comm_consent = Consent(
                applicant_id=candidate.id,
                consent_type="communication",
                consent_text_version="v2026.1",
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) # naive datetime
            )
            db.add(comm_consent)

        # Güncelleme zamanını mühürlüyoruz
        candidate.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # 7. DB Mühürleme (Atomic işlem)
        await db.commit()
        await db.refresh(candidate)
        return candidate

    except Exception as e:
        await db.rollback()
        # Güvenli hata mesajı
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gölge aday profilini tamamlama esnasında bir hata oluştu: {str(e)}"
        )