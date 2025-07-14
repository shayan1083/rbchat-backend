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
from langchain.text_splitter import RecursiveCharacterTextSplitter
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

def ensure_uploaded_files_table():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        data JSONB NOT NULL,
        upload_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with psycopg2.connect(**connection_params) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)


async def process_file(file: UploadFile, session_id: str) -> dict:
    filename = file.filename
    file_extension = Path(filename).suffix.lower()
    
    content = await file.read()

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    processed_data = None
    
    if file_extension in ['.csv']:
        df = pd.read_csv(io.BytesIO(content))
        processed_data = df.replace({np.nan: None}).to_dict('records')
        file_type = "csv"
        
    elif file_extension in ['.xlsx', '.xls']:
        df = pd.read_excel(io.BytesIO(content))
        processed_data = df.to_dict('records')
        file_type = "excel"
        
    elif file_extension in ['.json']:
        processed_data = json.loads(content.decode('utf-8'))
        file_type = "json"
        
    elif file_extension in ['.txt']:
        processed_data = content.decode('utf-8')
        file_type = "text"
   
    elif file_extension in ['.pdf']:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text_content = "".join([page.extract_text() for page in pdf_reader.pages])
        processed_data = text_content
        file_type = "pdf"
        
    else:
        logger.error(f'[FILE UPLOAD] Unsupported file type: {file_extension}')
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
    

    with psycopg2.connect(**connection_params) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO uploaded_files (session_id, filename, file_type, data, upload_time)
                VALUES (%s, %s, %s, %s, %s);
            """, (
                session_id,
                filename,
                file_type,
                json.dumps(processed_data),
                datetime.now()
            ))
    
    return {
        "message": "File uploaded and processed successfully",
        "session_id": session_id,
        "file_type": file_type,
        "filename": filename
    }

def get_uploaded_data(session_id: str):
    with psycopg2.connect(**connection_params) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT data, file_type, filename FROM uploaded_files WHERE session_id = %s ORDER BY upload_time DESC LIMIT 1",
                (session_id,)
            )
            result = cur.fetchone()
            file_dict = {}
            if result:
                file_dict = {
                    "data": result[0],  # JSON string
                    "file_type": result[1],
                    "filename": result[2],
                }
                file_dict = chunk_file(file_dict)
                return file_dict

            return None


def chunk_file(uploaded_data: dict, chunk_size: int = 500):
    data = uploaded_data['data']
    
    # If data is a list of dicts, convert to CSV format
    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        import pandas as pd
        df = pd.DataFrame(data)
        data = df.to_csv(index=False)
    
    elif not isinstance(data, str):
        # Fallback: stringify any other non-string content
        data = json.dumps(data, indent=2)

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=50)
    chunks = splitter.split_text(data)
    
    uploaded_data['chunks'] = "\n\n".join(chunks)
    return uploaded_data

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