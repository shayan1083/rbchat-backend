from custom_logging.llm_logger import LLMLogger
from repositories.user_repository import UserRepository
from fastapi import HTTPException
from models.models import UserResetRequest, User, VerifyResetRequest, UpdatePasswordRequest
from config.settings import Settings
from utils.hash import generate_reset_code
from repositories.metadata_repository import MetadataRepository
from repositories.user_repository import UserRepository
from service.email_service import send_email_smtp
from models.email_models import EmailParams, EmailType
from datetime import datetime, timezone
from utils.hash import hash_password

settings = Settings()
logger = LLMLogger()

def increment_account_lock(user: User):
    retries = user.account_lock_retries + 1
    if retries >= settings.MAX_ACCOUNT_LOCK_RETRIES:
        with UserRepository() as repo:
            repo.lock_account(user.id)
        logger.info(f"(API) Account locked due to too many failed login attempts: {user.email}")
        raise HTTPException(status_code=403, detail="Account is locked due to too many failed login attempts")
    else:
        with UserRepository() as repo:
            repo.increment_account_lock_retries(user.id)
        logger.info(f"(API) Incremented account lock retries for user: {user.email} to {retries}")
        raise HTTPException(status_code=401, detail=f"Incorrect password, {settings.MAX_ACCOUNT_LOCK_RETRIES - retries} attempts left")
    
def reset_account_lock(user: User):
    if user.account_lock_retries > 0:
        with UserRepository() as repo:
            repo.reset_account_lock_retries(user.id)
        logger.info(f"(API) Reset account lock retries for user: {user.email}")

def send_reset_code(user: UserResetRequest):
    with UserRepository() as repo:
        user_obj = repo.get_user_by_email(user.email)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    
    reset_code = generate_reset_code()
    with MetadataRepository() as meta_repo:
        inserted = meta_repo.insert_reset_code(user_obj['id'], reset_code)

    if not inserted:
        raise HTTPException(status_code=500, detail="Could not generate reset code, please try again later")

    email_params = EmailParams(
        to_email=user_obj['email'],
        subject="Your Password Reset Code",
        payload={
            "code": reset_code
        },
        email_type=EmailType.RESET_PASSWORD
    )
    sent = send_email_smtp(email_params)
    if not sent:
        raise HTTPException(status_code=500, detail="Could not send reset code email, please try again later")
    
    return {"message": "Reset code sent to your email"}
    
def verify_reset_code(user: VerifyResetRequest):
    with MetadataRepository() as meta_repo:
        password_reset_obj = meta_repo.get_password_reset_obj(user.email)
    
    if not password_reset_obj:
        raise HTTPException(status_code=404, detail="Could not find user in password request table")
    
    if datetime.now(timezone.utc) >= password_reset_obj['expires_at']:
        raise HTTPException(status_code=400, detail="Reset code expired")

    if user.reset_code.strip() != password_reset_obj['reset_code']:
        raise HTTPException(status_code=400, detail="Incorrect reset code")
    
    return {"message": "Reset code verified"}


def update_password(user: UpdatePasswordRequest):
    with MetadataRepository() as meta_repo:
        password_reset_obj = meta_repo.get_password_reset_obj(user.email)

    if not password_reset_obj:
        raise HTTPException(status_code=404, detail="Could not find user in password request table")
    
    if datetime.now(timezone.utc) >= password_reset_obj['expires_at']:
        raise HTTPException(status_code=400, detail="Reset code expired")
    
    if user.reset_code.strip() != password_reset_obj['reset_code']:
        raise HTTPException(status_code=400, detail="Incorrect reset code")
    
    hashed_password = hash_password(user.password)
    with UserRepository() as user_repo:
        user_repo.update_user_password(user.email, hashed_password)

    email_params = EmailParams(
        to_email=user.email,
        subject="Your Password Was Updated",
        payload={
            "reset_link": 'http://localhost:5173/reset-password'
        },
        email_type=EmailType.PASSWORD_CHANGED
    )
    sent = send_email_smtp(email_params)
    if not sent:
        raise HTTPException(status_code=500, detail="Could not send reset code email, please try again later")
    
    return {"message": "Reset code sent to your email"}
    

