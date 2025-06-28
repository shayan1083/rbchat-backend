import logging
import psycopg2
from datetime import datetime, timezone
from settings import Settings
from postgres_logging import PostgresHandler

settings = Settings()

logger = logging.getLogger("llm_logger")
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logger.setLevel(log_level)

connection_params = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "dbname": settings.DB_NAME,
        }

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
    except Exception as e:
        logger.error(f"Failed to create llm_logs table: {e}")
    finally:
        if conn:
            conn.close()

def log_llm_use(model_name: str, prompt: str, response: str, input_tokens: int, output_tokens: int, total_tokens: int, tool_name: str = None):
    conn = psycopg2.connect(
            **connection_params,
        )
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO llm_logs (timestamp, model_name, prompt, response, input_tokens, output_tokens, total_tokens, tool_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    datetime.now(timezone.utc), model_name, prompt, response, input_tokens, output_tokens, total_tokens, tool_name
                ))
        
    except Exception as e:
        logger.error(f"Failed to log to PostgreSQL: {e}")
    finally:
        if conn:
            conn.close()

def log_info(message: str):
    logger.info(f"{message}", stacklevel=2)

def log_error(message: str):
    logger.error(f"{message}", exc_info=True, stacklevel=2)

def log_tool_start(tool_name: str):
    logger.info(f"[Tool Start] {tool_name} started", stacklevel=2)

def log_tool_end(tool_name: str, output: str = None):
    logger.info(f"[Tool End] {tool_name} completed", stacklevel=2)
    if output:
        logger.info(f"[Tool Output] {output}", stacklevel=2)

def log_sql_output(sql_query: str):
    logger.info(f"[SQL Query] {sql_query}", stacklevel=2)

# Main usage logging
def log_llm_usage(model_name: str, prompt: str, response: str, token_usage: dict, tool_used: str = None):
    logger.info(f"[LLM] Model: {model_name}", stacklevel=2)
    logger.info(f"[LLM] Prompt: {prompt}", stacklevel=2)
    logger.info(f"[LLM] Response: {response}", stacklevel=2)
    logger.info(
        f"[Usage] Tokens - Input: {token_usage.get('input_tokens')}, "
        f"Output: {token_usage.get('output_tokens')}, "
        f"Total: {token_usage.get('total_tokens')}"
    )
    log_llm_use(
        model_name=model_name,
        prompt=prompt,
        response=response,
        input_tokens=token_usage.get("input_tokens"),
        output_tokens=token_usage.get("output_tokens"),
        total_tokens=token_usage.get("total_tokens"),
        tool_name=tool_used
    )

if settings.ENABLE_LOGGING and not logger.handlers:
    pg_handler = PostgresHandler(connection_params)
    pg_handler.setLevel(log_level)
    logger.addHandler(pg_handler)

    ensure_llm_logs_table()