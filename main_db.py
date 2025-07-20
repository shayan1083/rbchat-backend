from settings import Settings
import psycopg2
from llm_logger import LLMLogger
from db_memory import ensure_chat_history_table_exists

settings = Settings()

logger = LLMLogger()

connection_params = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "dbname": settings.DB_NAME,
}

def create_tables():
    ensure_app_logs_exists()
    ensure_llm_logs_table()
    ensure_chat_history_table_exists() 
    ensure_uploaded_files_table()
    ensure_modified_files_table()
    ensure_db_table()
    


def ensure_db_table():
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS available_databases (
        id SERIAL PRIMARY KEY,
        database_name TEXT NOT NULL UNIQUE,
        description TEXT,
        default_db BOOLEAN NOT NULL DEFAULT FALSE
    );
    """
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
        logger.info('(API) Ensured available_databases exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring available_databases exists: {e}')

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
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
        logger.info('(API) Ensured uploaded_files exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring uploaded_files exists: {e}')

def ensure_llm_logs_table():
        try:
            conn = psycopg2.connect(**connection_params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS llm_logs (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP with time zone,
                            model_name TEXT NOT null,
                            prompt TEXT NOT NULL,
                            response TEXT NOT NULL,
                            input_tokens INT,
                            output_tokens INT,
                            total_tokens INT,
                            tool_name TEXT
                        );
                    """)
            logger.info("(API) llm_logs table ensured successfully.")
        except Exception as e:
            logger.error(f"(API) Failed to create llm_logs table: {e}")
    
def ensure_app_logs_exists():
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS app_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            logger_name TEXT,
            module TEXT,
            function TEXT,
            line_number INT
        );
        """
        conn = None
        try:
            conn = psycopg2.connect(**connection_params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
            logger.info("(API) Ensured app_logs table exists")
        except Exception as e:
            print(f"(API) Failed to ensure app_logs exists: {e}")
        finally:
            if conn:
                conn.close()

def ensure_modified_files_table():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS modified_files (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        content BYTEA,              
        data JSONB,           
        upload_time TIMESTAMPTZ DEFAULT NOW()
    );
    """
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
        logger.info('(API) Ensured modified_files exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring modified_files table: {e}')
