import psycopg2
from config.settings import Settings
from custom_logging.llm_logger import LLMLogger

settings = Settings()
logger = LLMLogger()

class LogRepository:
    def __init__(self, dbname: str = settings.DB_NAME):
        self.connection_params = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "dbname": dbname,
        }
        self.conn = None
        try:
            self.conn = psycopg2.connect(**self.connection_params)
        except Exception as e:
            logger.error(f"[LogRepository] Failed to connect to database: {e}")
        
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()

    def estimate_tokens(self):
        #logger.info('(API) Fetching token amount of last call')
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                               SELECT total_tokens
                               FROM llm_logs
                               ORDER BY timestamp DESC
                               LIMIT 1
                               """)
                row = cursor.fetchone()
        except Exception as e:
            logger.error(f"(API) Failed to get last token call usage: {e}")
            return 0

        if row and row[0] is not None:
            return row[0]
        else:
            return 15000
        

    def get_app_logs(self, limit: int = 20, offset: int = 0):
        #logger.info('(API) Fetching App Logs')
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                               a.timestamp, 
                               u.email, 
                               a.level, 
                               a.message, 
                               a.module, 
                               a.function, 
                               a.line_number
                    FROM app_logs a
                    LEFT JOIN users u ON a.user_id = u.id
                    ORDER BY a.timestamp DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                col_names = [desc[0] for desc in cursor.description]
                logs = [dict(zip(col_names, row)) for row in cursor.fetchall()]

                cursor.execute("SELECT COUNT(*) FROM app_logs")
                total_count = cursor.fetchone()[0]

                return logs, total_count
        except Exception as e:
            logger.error(f"Error fetching app logs: {e}")
            return [], 0