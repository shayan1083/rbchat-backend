from pydantic import BaseModel
from enum import Enum

class EmailType(Enum):
    SIGNUP = "signup"
    RESET_PASSWORD = "password"
    PASSWORD_CHANGED = "password_changed"


class EmailParams(BaseModel):
    to_email: str    
    subject: str        
    payload:dict = {}
    email_type:EmailType
    