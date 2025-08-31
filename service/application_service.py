from typing import Optional
from cachetools import TTLCache
from repositories.user_repository import UserRepository
from models.application_models import Application

_app_cache = TTLCache(maxsize=100, ttl=3600)

def get_application_info_cached(app_id: str) -> Optional[Application]:
    if app_id in _app_cache:       
        return _app_cache[app_id]
    else:        
        with UserRepository() as repo:
            res = repo.get_application_info(app_id)
            if not res:
                return None
            _app_cache[app_id] = res  
            return res