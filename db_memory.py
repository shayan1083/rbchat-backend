import uuid
import psycopg
from langchain_postgres import PostgresChatMessageHistory
from settings import Settings
from langchain_core.chat_history import BaseChatMessageHistory

settings = Settings()


def get_psycopg_conn():
    return psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME,
    )

# uncomment this and run this file to create the table 
# conn = get_psycopg_conn()
# PostgresChatMessageHistory.create_tables(conn, settings.DB_CHAT_HISTORY_TABLE)
# conn.close()

# Function to generate a session ID
def generate_session_id() -> str:
    return str(uuid.uuid4())

# Returns a ChatMessageHistory object tied to a session
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return PostgresChatMessageHistory(
        settings.DB_CHAT_HISTORY_TABLE,
        session_id,
        sync_connection=get_psycopg_conn()
    )