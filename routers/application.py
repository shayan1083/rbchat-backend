from fastapi import APIRouter, HTTPException
from config.settings import Settings
from custom_logging.llm_logger import LLMLogger

from service.application_service import get_application_info_cached

router = APIRouter()
logger = LLMLogger()
settings = Settings()


@router.get("/get_application/{id}")
def get_application(id: str):
    app = get_application_info_cached(id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return  {
            "name":app.name,
            "description" : app.description,
            "ids": [app.client_secret,app.client_id],
            "allow_registration": app.allow_registration,
            "scope": app.scope
    }      