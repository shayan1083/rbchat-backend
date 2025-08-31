from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config.settings import Settings
from custom_logging.llm_logger import LLMLogger
import uvicorn
from routers.auth import get_current_active_user
from database.main_db import create_tables
from repositories.user_repository import UserRepository
from routers.auth import router as auth_router, AuthMiddleware
from routers.chat import router as chat_router
from routers.logs import router as logs_router
from routers.users import router as users_router
from routers.application import router as application_router

from service.signup_service import register_user
from service.user_service import send_reset_code, verify_reset_code, update_password
from starlette.requests import Request
from models.models import UserSignup, UserResetRequest, VerifyResetRequest, UpdatePasswordRequest
from utils.exceptions import AppException, app_exception_handler, global_exception_handler

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=['auth'])
app.include_router(chat_router, prefix='/api/chat', dependencies=[Depends(get_current_active_user)], tags=['chat'])
app.include_router(logs_router, prefix='/logs', tags=['logs'])
app.include_router(users_router, prefix='/users', tags=['users'])
app.include_router(application_router, prefix='/application', tags=['application'])


app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

settings = Settings()

logger = LLMLogger()

create_tables()

logger.info('Starting API')

# Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

@app.post("/register")
async def signup(user:UserSignup, request: Request):
    return register_user(user, ip=request.client.host)

@app.post("/reset-code")
async def reset_code_endpoint(user: UserResetRequest):
    return send_reset_code(user)

@app.post("/verify-code")
async def verify_reset_code_endpoint(user: VerifyResetRequest):
    return verify_reset_code(user)

@app.post("/update-password")
async def update_password_endpoint(user: UpdatePasswordRequest):
    return update_password(user)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT)
    
# uvicorn main:app --reload --port 8003