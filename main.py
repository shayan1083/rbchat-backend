from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from client import run_agent#, call_llm
from fastapi.middleware.cors import CORSMiddleware
from settings import Settings
from db_memory import generate_session_id
from llm_logger import log_info, log_error
import uvicorn
from file_upload import process_file, get_uploaded_data, ensure_uploaded_files_table, get_file_from_temp_table
import io

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
session_data = {}


@app.get("/query")
async def query(
    prompt: str, 
    session_id: str = "default",
    ):
    log_info(f"[QUERY] /query endpoint hit | Session: {session_id} | Prompt: {prompt}")
    file_context = get_uploaded_data(session_id)
    return StreamingResponse(run_agent(prompt, session_id, file_context), media_type="text/event-stream")

@app.get("/session")
def new_session():
    new_id = generate_session_id()
    log_info(f"[SESSION] New session created: {new_id}")
    return {"session_id": new_id}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = "default"):
    try:
       ensure_uploaded_files_table()
       result = await process_file(file, session_id)
       log_info(f"[UPLOAD] New file uploaded")
       return result
    except Exception as e:
        log_error(f"[UPLOAD] Error processing file: {str(e)}")
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
    

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=True)
    
