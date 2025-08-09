from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic import BaseModel
from settings import Settings

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import jwt

from user_repository import UserRepository

settings = Settings()

router = APIRouter()

REFRESH_TOKEN='refresh_token'


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenWithRefresh(Token):
    refresh_token: str

class TokenData(BaseModel):
    username: str | None = None

class RefreshRequest(BaseModel):
    refresh_token: str


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    location: str | None = None
    lastLogin: str | None = None
    disabled: bool | None = None
    role: str | None = 'user'


class UserInDB(User):
    hashed_password: str


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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
                    request.state.user = payload.get("sub")  # Store user info
                except jwt.PyJWTError:
                    raise HTTPException(status_code=401, detail="Invalid token")
            else:
                raise HTTPException(status_code=401, detail="Invalid auth scheme")
        else:
            request.state.user = None  # Optional: allow anonymous access

        return await call_next(request)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    with UserRepository() as repo:
        user_dict = repo.get_user_by_username(username)
    if user_dict:
        return UserInDB(**user_dict)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    return user


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
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
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
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
   
    refresh_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=7)
    )

    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,          # Use only in production (HTTPS)
        samesite="lax",    # You can use "lax" if needed
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
        username = payload_data.get('sub')
        if username is None:
            raise HTTPException(status_code=401, detail='Invalid refresh token')
        
        user = get_user(username)
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        
        new_access_token = create_access_token(
            data={"sub":user.username, "role":user.role},
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