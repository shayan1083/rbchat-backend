from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from settings import Settings
from llm_logger import LLMLogger
import uvicorn
from auth import get_current_active_user
from main_db import create_tables

from auth import router as auth_router, AuthMiddleware
from chat import router as chat_router

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=['auth'])
app.include_router(chat_router, prefix='/api/chat', dependencies=[Depends(get_current_active_user)], tags=['chat'])

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


# if __name__ == "__main__":
#     uvicorn.run("main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT)
    
# uvicorn main:app --reload --port 8003