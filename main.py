from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from client import run_agent, call_llm
from fastapi.middleware.cors import CORSMiddleware
from settings import Settings
from db_memory import generate_session_id
from llm_logger import log_info
import uvicorn

from auth import router as auth_router, get_current_active_user

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import jwt

app = FastAPI()

app.include_router(auth_router, prefix="/auth")

settings = Settings()

# Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                    return JSONResponse(status_code=401, content={"detail": "Invalid token"})
            else:
                return JSONResponse(status_code=401, content={"detail": "Invalid auth scheme"})
        else:
            request.state.user = None  # Optional: allow anonymous access

        return await call_next(request)

app.add_middleware(AuthMiddleware)

@app.get("/query")
async def query(
    prompt: str, 
    # user=Depends(get_current_active_user),  
    session_id: str = "default",
    ):
    # log_info(f"[QUERY] /query endpoint hit | Session: {session_id} | User: {user.username} | Prompt: {prompt}")
    log_info(f"[QUERY] /query endpoint hit | Session: {session_id} | Prompt: {prompt}")
    return StreamingResponse(run_agent(prompt, session_id), media_type="text/event-stream")

@app.get("/queryllm")
async def queryllm(prompt: str, session_id: str = "default"):
    log_info(f"[QUERYLLM] /queryllm endpoint hit | Session: {session_id} | Prompt: {prompt}")
    return StreamingResponse(call_llm(prompt, session_id), media_type="text/event-stream")

@app.get("/session")
def new_session():
    new_id = generate_session_id()
    log_info(f"[SESSION] New session created: {new_id}")
    return {"session_id": new_id}

@app.post("/test")
def test():
    return {"message": "Test endpoint is working!"}

@app.get("/secure-data")
async def secure_data(request: Request):
    if not request.state.user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user": request.state.user, "message": "This is protected data"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=True)
    
