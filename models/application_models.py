from pydantic import BaseModel
from typing import List
from datetime import datetime

class Application(BaseModel):
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    active: bool
    client_secret: str
    client_id: str
    # ids: List[str]
    allow_registration: bool
    scope: str