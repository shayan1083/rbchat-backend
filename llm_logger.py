import logging
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
from settings import Settings

env_path = ".env"
load_dotenv(env_path)
settings = Settings()

logger = logging.getLogger("llm_logger")
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logger.setLevel(log_level)

if settings.ENABLE_LOGGING and not logger.handlers:

    file_handler = logging.FileHandler(settings.LOG_FILE, mode='a')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

connection_params = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "dbname": settings.DB_NAME,
        }

# --- Optional: Log to Database ---
def log_to_database(model_name: str, prompt: str, response: str, input_tokens: int, output_tokens: int, total_tokens: int, tool_name: str = None):
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

def log_debug(message: str):
    logger.debug(f"{message}")

def log_info(message: str):
    logger.info(f"{message}")

def log_error(message: str):
    logger.error(f"{message}")

def log_tool_start(tool_name: str):
    logger.info(f"[Tool Start] 🔧 {tool_name} started")

def log_tool_end(tool_name: str, output: str = None):
    logger.info(f"[Tool End] {tool_name} completed")
    if output:
        logger.info(f"[Tool Output] {output}")

def log_sql_output(sql_query: str):
    logger.info(f"[SQL Query] {sql_query}")

# Main usage logging
def log_llm_usage(model_name: str, prompt: str, response: str, token_usage: dict, tool_used: str = None):
    logger.info(f"[LLM] Model: {model_name}")
    logger.info(f"[LLM] Prompt: {prompt}")
    logger.info(f"[LLM] Response: {response}")
    logger.info(
        f"[Usage] Tokens - Input: {token_usage.get('input_tokens')}, "
        f"Output: {token_usage.get('output_tokens')}, "
        f"Total: {token_usage.get('total_tokens')}"
    )
    log_to_database(
        model_name=model_name,
        prompt=prompt,
        response=response,
        input_tokens=token_usage.get("input_tokens"),
        output_tokens=token_usage.get("output_tokens"),
        total_tokens=token_usage.get("total_tokens"),
        tool_name=tool_used
    )