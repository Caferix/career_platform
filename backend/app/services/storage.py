import os
import shutil
import uuid
import logging
from fastapi import UploadFile
from app.core.settings import settings

logger = logging.getLogger(__name__)

# backend/uploads/ klasörü yoksa proje çalışırken otomatik oluşturulur
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

async def save_file(file: UploadFile) -> str:

    """
    Gelen dosyayı UUID ile maskeler ve güvenli bir şekilde diske yazar.
    Geriye dosyanın yeni benzersiz adını döner.


    """
    # Uzantıyı ayıkla (Örn: .pdf)
    extension = os.path.splitext(file.filename)[1].lower()
    
    # Güvenlik Kontrolü: İzin verilen uzantılardan biri mi?
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"Geçersiz dosya uzantısı. İzin verilenler: {settings.ALLOWED_EXTENSIONS}")
        
    # Benzersiz yeni isim üret
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    try:
        # Senkron kopyalama bloğu (İleride asenkron yapılacak)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Dosya başarıyla diske mühürlendi: {unique_filename}")
        return unique_filename
    except Exception as e:
        logger.error(f"Fiziksel dosya yazma hatası: {str(e)}")
        raise RuntimeError("Dosya depolama sistemine yazılırken hata oluştu.")

def get_file_path(filename: str) -> str:
    """Verilen dosya adının diskteki tam yolunu güvenli bir şekilde birleştirir."""
    return os.path.join(settings.UPLOAD_DIR, filename)

def delete_file(filename: str) -> bool:
    """CV güncellendiğinde eski dosyanın diskte yer kaplamaması için fiziksel olarak siler."""
    if not filename:
        return False
    try:
        file_path = get_file_path(filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Eski dosya diskten temizlendi: {filename}")
            return True
        return False
    except Exception as e:
        logger.error(f"Dosya silinirken hata oluştu ({filename}): {str(e)}")
        return False
    
def get_file_url(filename: str) -> str:
    """Dosya adından erişilebilir URL üretir."""
    return f"{settings.BASE_URL}/uploads/{filename}"    