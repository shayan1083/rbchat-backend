from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from client import run_agent
from fastapi.middleware.cors import CORSMiddleware
from settings import Settings
from db_memory import generate_session_id
from llm_logger import LLMLogger
import uvicorn
from file_upload import process_file, get_uploaded_data, ensure_uploaded_files_table, get_file_from_temp_table
import io
from TokenTracker import TokenUsageTracker
from user_repository import UserRepository
from db_memory import ensure_chat_history_table_exists

app = FastAPI()



settings = Settings()

logger = LLMLogger()

ensure_uploaded_files_table()
ensure_chat_history_table_exists()
logger.info('Starting API')

token_tracker = TokenUsageTracker(limit_per_minute=30000)

# Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/query")
async def query(prompt: str, session_id: str, db_name: str):
    logger.info(f"(API) /query endpoint hit | Session: {session_id}")
    # with UserRepository() as repo:
    #     estimated_tokens_needed = repo.estimate_tokens()

    # if not token_tracker.can_process(estimated_tokens_needed):
    #     logger.error("(API) Token limit exceeded. Request denied.")
    #     async def error_stream():
    #         yield f"RATE_LIMIT_ERROR: Too many requests are being processed, please wait 30 seconds.\n\n"
    #     return StreamingResponse(error_stream(), media_type="text/event-stream")

    # token_tracker.add_usage(estimated_tokens_needed)
    
    file_context = get_uploaded_data(session_id, db_name)
    return StreamingResponse(run_agent(prompt, session_id, file_context, db_name), media_type="text/event-stream")


@app.get("/session")
def new_session():
    new_id = generate_session_id()
    logger.info(f"(API) New session created: {new_id}")
    return {"session_id": new_id}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = "default"):
    try:
       result = await process_file(file, session_id)
       logger.info(f"(API) New file uploaded")
       return result
    except Exception as e:
        logger.error(f"(API) Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    

@app.get("/download/{id}")
def download_file(id: int):
    file_record = get_file_from_temp_table(id)

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if not file_record["content"]:
        raise HTTPException(status_code=404, detail="No binary content available")

    return StreamingResponse(
        io.BytesIO(file_record["content"]),
        media_type=file_record["file_type"],
        headers={"Content-Disposition": f"attachment; filename={file_record['filename']}"}
    )
    
@app.get("/database_names")
def get_database_names():
    with UserRepository() as repo:
        db_names = repo.get_database_names()
    if not db_names:
        raise HTTPException(status_code=404, detail="No databases found")
    return {"databases": db_names}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=True)
    
