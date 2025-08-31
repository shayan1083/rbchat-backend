from fastapi import APIRouter, Depends
from config.settings import Settings
from custom_logging.llm_logger import LLMLogger
from routers.auth import role_required, User

from repositories.log_repository import LogRepository

router = APIRouter()
logger = LLMLogger()
settings = Settings()


