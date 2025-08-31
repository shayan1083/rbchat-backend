from fastapi import APIRouter, Depends
from config.settings import Settings
from custom_logging.llm_logger import LLMLogger
from routers.auth import role_required, User

from repositories.log_repository import LogRepository

router = APIRouter()
logger = LLMLogger()
settings = Settings()

@router.get("/app-logs")
def get_log_history(
    user: User = Depends(role_required(["admin"])),
    limit: int = 25,
    offset: int = 0
    ):
    with LogRepository() as repo:
        data, total_count = repo.get_app_logs(limit=limit, offset=offset)
    
    return {
        "logs": data,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }
