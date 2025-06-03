from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from client import run_agent, call_llm
from fastapi.middleware.cors import CORSMiddleware
from settings import Settings

app = FastAPI()

settings = Settings()

# Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/query")
async def query(prompt: str, session_id: str = "default"):
    return StreamingResponse(run_agent(prompt), media_type="text/event-stream")

@app.get("/queryllm")
async def queryllm(prompt: str, session_id: str = "default"):
    return StreamingResponse(call_llm(prompt), media_type="text/event-stream")


# uvicorn main:app --reload --host 8003
