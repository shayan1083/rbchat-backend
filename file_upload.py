from fastapi import UploadFile, HTTPException
from settings import Settings
from llm_logger import LLMLogger
import json
from pathlib import Path
import pandas as pd
import io
import PyPDF2
from settings import Settings
import psycopg2
from datetime import datetime
from user_repository import UserRepository

import numpy as np

settings = Settings()

logger = LLMLogger()

connection_params = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "dbname": settings.DB_NAME,
}



async def process_file(file: UploadFile, session_id: str) -> dict:
    filename = file.filename
    file_extension = Path(filename).suffix.lower()
    
    content = await file.read()

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    processed_data = None
    
    # if file_extension in ['.csv']:
    #     df = pd.read_csv(io.BytesIO(content))
    #     processed_data = df.replace({np.nan: None}).to_dict('records')
    #     file_type = "csv"
        
    # if file_extension in ['.xlsx', '.xls']:
    #     df = pd.read_excel(io.BytesIO(content))
    #     # processed_data = df.to_dict('records')
    #     processed_data = df.replace({np.nan: None}).to_dict(orient='records')

        
    # elif file_extension in ['.json']:
    #     processed_data = json.loads(content.decode('utf-8'))
    #     file_type = "json"
        
    #elif file_extension in ['.txt']:
    # else:
    processed_data = content.decode('utf-8')
        #file_type = "text"
   
    # elif file_extension in ['.pdf']:
    #     pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    #     text_content = "".join([page.extract_text() for page in pdf_reader.pages])
    #     processed_data = text_content
    #     file_type = "pdf"
        
    # else:
    #     logger.error(f'[FILE UPLOAD] Unsupported file type: {file_extension}')
    #     raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
    

    with psycopg2.connect(**connection_params) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO uploaded_files (session_id, filename, file_type, data, upload_time)
                VALUES (%s, %s, %s, %s, %s);
            """, (
                session_id,
                filename,
                file_extension,
                json.dumps(processed_data),
                datetime.now()
            ))
    
    return {
        "message": "File uploaded and processed successfully",
        "session_id": session_id,
        "file_type": file_extension,
        "filename": filename
    }

def get_uploaded_data(session_id: str) -> dict:
    with UserRepository() as repo:
        logger.info(f"(API) Fetching uploaded data for session: {session_id}") 
        file_dict = repo.get_uploaded_data(session_id)
        return file_dict

def get_file_from_temp_table(id: int):
    query = """
        SELECT filename, file_type, content
        FROM modified_files
        WHERE id = %s
    """
    params = [id]

    with psycopg2.connect(**connection_params) as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            result = cur.fetchone()
            if not result:
                return None
            return {
                "filename": result[0],
                "file_type": result[1],
                "content": result[2]
            }