from pydantic import BaseModel

class UserSignup(BaseModel):
    email: str
    password: str
    client_id: str

class UserResetRequest(BaseModel):
    email: str

class VerifyResetRequest(BaseModel):
    email: str
    reset_code: str

class UpdatePasswordRequest(BaseModel):
    email: str
    reset_code: str
    password: str


class User(BaseModel):
    id: str
    email: str = None
    fname: str | None = None
    lname: str | None = None
    role: str = 'user'
    location: str | None = None
    lastLogin: str | None = None
    created_at: str | None = None
    email_verified: bool = None
    email_verification_date: str | None = None
    account_locked: bool = False
    account_lock_date: str | None = None
    account_lock_retries: int = 0
    client_id: str | None = None