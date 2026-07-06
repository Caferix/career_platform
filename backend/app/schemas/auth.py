from pydantic import BaseModel, Field, EmailStr

class SendOTPRequest(BaseModel):
    """Kullanıcı sadece telefon numarasını girerek kod ister"""
    phone: str = Field(..., description="Uluslararası formatta telefon numarası (Örn: +905510385838)")
    kvkk_approved: bool

class VerifyOTPRequest(BaseModel):
    """Kullanıcı kodu doğrulamak için hem telefonunu hem gelen kodu gönderir"""
    phone: str = Field(..., description="Kodun gönderildiği telefon numarası")
    code: str = Field(..., min_length=6, max_length=6, description="6 haneli SMS doğrulama kodu")

class TokenResponse(BaseModel):
    """Doğrulama başarılıysa frontend'e döneceğimiz bilet formatı"""
    access_token: str
    token_type: str = "bearer"


class AdminLoginRequest(BaseModel):
    login_name: str = Field(..., description="Kurumsal kullanıcı adı (Örn: hr_admin)")
    password: str = Field(..., description="Ham şifre")