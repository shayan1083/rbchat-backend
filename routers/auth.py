from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from utils.hash import verify_password
from pydantic import BaseModel
from config.settings import Settings

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import jwt

from repositories.user_repository import UserRepository
from service.user_service import increment_account_lock, reset_account_lock

from utils.context import current_user_id

settings = Settings()

router = APIRouter()

REFRESH_TOKEN='refresh_token'

from models.models import User

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenWithRefresh(Token):
    refresh_token: str

class TokenData(BaseModel):
    email: str | None = None

class RefreshRequest(BaseModel):
    refresh_token: str


# class User(BaseModel):
#     id: str
#     email: str | None = None
#     full_name: str | None = None
#     role: str | None = 'user'
#     lastLogin: str | None = None
#     disabled: bool | None = None
#     created_at: str | None = None



class UserInDB(User):
    hashed_password: str


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            scheme, _, token = auth_header.partition(" ")
            if scheme.lower() == "bearer":
                try:
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=[settings.ALGORITHM]
                    )
                    user_id = payload.get("user_id")
                    request.state.user = payload.get("sub")  # Store user info
                    request.state.token = token
                except jwt.PyJWTError:
                    raise HTTPException(status_code=401, detail="Invalid token")
            else:
                raise HTTPException(status_code=401, detail="Invalid auth scheme")
        else:
            request.state.user = None 
            request.state.token = None
        current_user_id.set(user_id)
        return await call_next(request)


# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# def verify_password(plain_password, hashed_password):
#     # return pwd_context.verify(plain_password, hashed_password)
#     return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_user(email: str):
    with UserRepository() as repo:
        user_dict = repo.get_user_by_email(email)
    if user_dict:
        return UserInDB(**user_dict)

def authenticate_user(email: str, password: str, client_id: str = None, client_secret: str = None, scopes: list[str] = None):
    with UserRepository() as repo:
        res = repo.get_application_info(client_id)
        if res:
            if not res.active:
                raise HTTPException(status_code=403, detail="Invalid Application")
            if res.client_secret != client_secret:
                raise HTTPException(status_code=403, detail="Invalid email and password")
            user = get_user(email)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if user.account_locked:
                raise HTTPException(status_code=403, detail="Account is locked")
            if not verify_password(password, user.hashed_password):
                increment_account_lock(user)
                raise HTTPException(status_code=401, detail="Incorrect password")
            reset_account_lock(user)
            return user
        else:
            raise HTTPException(status_code=404, detail="Application not found")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.account_locked:
        raise HTTPException(status_code=400, detail="Account is locked")
    return current_user

def role_required(required_roles: list[str]):
    def role_checker(user: Annotated[User, Depends(get_current_active_user)]):
        if user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(email=form_data.username, password=form_data.password, client_id=form_data.client_id, client_secret=form_data.client_secret, scopes=form_data.scopes)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
   
    refresh_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=7)
    )

    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,          
        samesite="lax",
        max_age=7 * 24 * 3600, 
    )

    return response

@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: Request):
    refresh_token = request.cookies.get(REFRESH_TOKEN)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        payload_data = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email = payload_data.get('sub')
        if email is None:
            raise HTTPException(status_code=401, detail='Invalid refresh token')
        
        user = get_user(email)
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        
        new_access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return Token(access_token=new_access_token, token_type="bearer")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='Invalid refresh token')

@router.get("/logout")
async def logout_user(response: Response):
    response = JSONResponse(content={"detail": "Logged out successfully"})
    response.delete_cookie(key="refresh_token",)
    return response

@router.get("/user/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

