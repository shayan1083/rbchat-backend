import uuid
import psycopg
from langchain_postgres import PostgresChatMessageHistory
from settings import Settings
from langchain_core.chat_history import BaseChatMessageHistory
from llm_logger import LLMLogger

settings = Settings()

logger = LLMLogger()


def get_psycopg_conn():
    return psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME,
    )

def ensure_chat_history_table_exists():
    conn = get_psycopg_conn()
    try:
        PostgresChatMessageHistory.create_tables(conn, settings.DB_CHAT_HISTORY_TABLE)
        logger.info(f"(API) Ensured chat history table '{settings.DB_CHAT_HISTORY_TABLE}' exists.")
    finally:
        conn.close()

# Function to generate a session ID
def generate_session_id() -> str:
    return str(uuid.uuid4())

# Returns a ChatMessageHistory object tied to a session
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    logger.info("(API) Getting Session History")
    return PostgresChatMessageHistory(
        settings.DB_CHAT_HISTORY_TABLE,
        session_id,
        sync_connection=get_psycopg_conn()
    )