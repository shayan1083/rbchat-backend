import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

env_path = ".env"
load_dotenv(env_path)

class Settings(BaseSettings):
    # Chat history memory
    MEMORY_LIMIT: int = int(os.getenv('MEMORY_LIMIT', 10))
    
    # Database configuration
    DB_HOST: str = os.getenv('DB_HOST')
    DB_PORT: int = int(os.getenv('DB_PORT'))
    DB_USER: str = os.getenv('DB_USER')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DB_NAME: str = os.getenv('DB_NAME')
    DB_CHAT_HISTORY_TABLE: str = os.getenv('DB_CHAT_HISTORY_TABLE')

    MCP_SERVER_HOST: str = os.getenv('MCP_SERVER_HOST')
    MCP_SERVER_PORT: str = os.getenv('MCP_SERVER_PORT')
    MCP_SERVER_URL: str = f"http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/mcp-server/mcp"
    
    ALLOWED_ORIGINS: str = os.getenv('ALLOWED_ORIGINS', '*')
    FASTAPI_HOST: str = os.getenv('FASTAPI_URL', "127.0.0.1")
    FASTAPI_PORT: int = int(os.getenv('FASTAPI_PORT', 8003))
    
    ENABLE_LOGGING: bool= os.getenv('ENABLE_LOGGING')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    # SQL Generation Prompt Configuration
    DIALECT: str = os.getenv('SQL_DIALECT')
    TOP_K: int = int(os.getenv('SQL_TOP_K'))
    EXPORT_TOP_K: int = int(os.getenv('EXPORT_TOP_K'))
    NEWLINE_CHAR: str = os.getenv('NEWLINE_CHAR', '^')

    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE',5242880))

    SECRET_KEY: str = os.getenv('AUTH_SECRET_KEY')
    ALGORITHM: str = os.getenv('HASH_ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
