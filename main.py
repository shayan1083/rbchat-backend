from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from client import run_agent, call_llm
from fastapi.middleware.cors import CORSMiddleware
from settings import Settings
from db_memory import generate_session_id
from llm_logger import log_info
import uvicorn

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

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=True)
# uvicorn main:app --reload --host 8003
