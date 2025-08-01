from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# env_path = ".env"
load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    # Chat history memory
    MEMORY_LIMIT: int = 10
    
    # Database configuration
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'postgres'
    DB_PASSWORD: str 
    DB_NAME: str = 'main'
    DB_CHAT_HISTORY_TABLE: str = 'chat_history'

    MCP_SERVER_HOST: str 
    MCP_SERVER_PORT: str 
    
    
    ALLOWED_ORIGINS: str = 'http://localhost:5173'
    FASTAPI_HOST: str 
    FASTAPI_PORT: int
    
    ENABLE_LOGGING: bool = True
    LOG_LEVEL: str = 'INFO'

    # SQL Generation Prompt Configuration
    DIALECT: str = 'postgresql'
    TOP_K: int = 20
    EXPORT_TOP_K: int = 10000
    NEWLINE_CHAR: str  = '^'
    FOLLOWUP_CHAR: str = '~'

    MAX_FILE_SIZE: int = 5242880

    @property
    def MCP_SERVER_URL(self) -> str:
        return f"http://{self.MCP_SERVER_HOST}:{self.MCP_SERVER_PORT}/mcp-server/mcp"

    class Config:
        env_file = ".env"
        extra = "allow"
