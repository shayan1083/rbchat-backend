import os
from dotenv import load_dotenv

env_path = ".env"
load_dotenv(env_path)

class Settings:
    # Database configuration
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = int(os.getenv('DB_PORT'))
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    MCP_SERVER_URL=os.getenv('MCP_SERVER_URL')
    MCP_SERVER_PORT=os.getenv('MCP_SERVER_PORT')
    ALLOWED_ORIGINS=os.getenv('ALLOWED_ORIGINS')