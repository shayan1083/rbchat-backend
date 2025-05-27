from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.client import run_agent, call_llm
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI

app = FastAPI()

raw_model = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
)

# Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/query")
async def query(prompt: str):
    return StreamingResponse(run_agent(prompt), media_type="text/event-stream")

@app.get("/queryllm")
async def queryllm(prompt: str):
    return StreamingResponse(call_llm(prompt), media_type="text/event-stream")


# uv run uvicorn app.main:app --reload --host 8003
