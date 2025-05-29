from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from client import run_agent, call_llm
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
import os

app = FastAPI()

raw_model = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
)

front_end = os.getenv("FRONT_END_URL")

# Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[front_end],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/query")
async def query(prompt: str):
    return StreamingResponse(run_agent(prompt), media_type="text/event-stream")

# commented out to avoid wasted chatgpt calls when testing mcp
# @app.get("/queryllm")
# async def queryllm(prompt: str):
#     return StreamingResponse(call_llm(prompt), media_type="text/event-stream")


# uvicorn main:app --reload --host 8003
