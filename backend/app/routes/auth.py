from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.core.departments import parse_departments
from app.core.settings import settings
from app.db.database import get_db
from app.schemas.auth import SendOTPRequest, TokenResponse, VerifyOTPRequest
from app.schemas.user import LoginRequest
from app.services import auth as token_service
from app.services import otp, sms
from app.services.user import authenticate_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.login_name, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )

    expires_delta = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = token_service.create_token(
        user_id=user.id,
        role=user.role,
        department=user.department,
        extra_claims={"departments": parse_departments(user.department) or []},
        expires_delta=expires_delta,
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/send-otp", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def send_otp(request: Request, payload: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    if not payload.kvkk_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KVKK onayı olmadan işlem yapılamaz."
        )

    code = otp.generate_otp()
    await otp.save_otp(db, phone=payload.phone, code=code)

    sms_sent = await sms.send_sms(phone=payload.phone, code=code)
    if not sms_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doğrulama kodu gönderilemedi. Lütfen daha sonra tekrar deneyin."
        )

    return {"message": "Doğrulama kodu başarıyla gönderildi."}


@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit("5/minute")
async def verify_otp(request: Request, payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    is_valid = await otp.verify_otp(db, phone=payload.phone, code=payload.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş doğrulama kodu."
        )

    access_token = token_service.create_token(
        user_id=0,
        role="applicant",
        extra_claims={"phone": payload.phone},
        expires_delta=timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS),
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
