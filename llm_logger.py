import logging
import psycopg2
from datetime import datetime, timezone
from settings import Settings
from postgres_logging import PostgresHandler


# logger = logging.getLogger("llm_logger")
# log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
# logger.setLevel(log_level)

# connection_params = {
#             "host": settings.DB_HOST,
#             "port": settings.DB_PORT,
#             "user": settings.DB_USER,
#             "password": settings.DB_PASSWORD,
#             "dbname": settings.DB_NAME,
#         }

# def ensure_llm_logs_table():
#     try:
#         conn = psycopg2.connect(**connection_params)
#         with conn:
#             with conn.cursor() as cur:
#                 cur.execute("""
#                     CREATE TABLE IF NOT EXISTS llm_logs (
#                         id SERIAL PRIMARY KEY,
#                         timestamp TIMESTAMP with time zone,
#                         model_name TEXT NOT null,
#                         prompt TEXT NOT NULL,
#                         response TEXT NOT NULL,
#                         input_tokens INT,
#                         output_tokens INT,
#                         total_tokens INT,
#                         tool_name TEXT
#                     );
#                 """)
#     except Exception as e:
#         logger.error(f"Failed to create llm_logs table: {e}")
#     finally:
#         if conn:
#             conn.close()

# def log_llm_use(model_name: str, prompt: str, response: str, input_tokens: int, output_tokens: int, total_tokens: int, tool_name: str = None):
#     conn = psycopg2.connect(
#             **connection_params,
#         )
#     try:
#         with conn:
#             with conn.cursor() as cur:
#                 cur.execute("""
#                     INSERT INTO llm_logs (timestamp, model_name, prompt, response, input_tokens, output_tokens, total_tokens, tool_name)
#                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
#                 """, (
#                     datetime.now(timezone.utc), model_name, prompt, response, input_tokens, output_tokens, total_tokens, tool_name
#                 ))
        
#     except Exception as e:
#         logger.error(f"Failed to log to PostgreSQL: {e}")
#     finally:
#         if conn:
#             conn.close()

# def log_info(message: str):
#     logger.info(message, stacklevel=2)

# def log_error(message: str):
#     logger.error(message, stacklevel=2)

# def setup_logger():
#     if settings.ENABLE_LOGGING:
#         if not any(isinstance(h, PostgresHandler) for h in logger.handlers):
#             pg_handler = PostgresHandler(connection_params)
#             pg_handler.setLevel(log_level)
#             logger.addHandler(pg_handler)
#         ensure_llm_logs_table()
#     return logger

# if settings.ENABLE_LOGGING and not logger.handlers:
#     pg_handler = PostgresHandler(connection_params)
#     pg_handler.setLevel(log_level)
#     logger.addHandler(pg_handler)
#     print("logger_handler", logger.handlers)

#     ensure_llm_logs_table()


class LLMLogger:
    def __init__(self):
        self.settings = Settings()

        self.logger = logging.getLogger("llm_logger")
        log_level = getattr(logging, self.settings.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        self.connection_params = {
            "host": self.settings.DB_HOST,
            "port": self.settings.DB_PORT,
            "user": self.settings.DB_USER,
            "password": self.settings.DB_PASSWORD,
            "dbname": self.settings.DB_NAME,
        }

        if self.settings.ENABLE_LOGGING and not self.logger.handlers:
            pg_handler = PostgresHandler(self.connection_params)
            pg_handler.setLevel(log_level)
            self.logger.addHandler(pg_handler)

            self.ensure_llm_logs_table()
        
    
    def ensure_llm_logs_table(self):
        try:
            conn = psycopg2.connect(**self.connection_params)
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
            self.logger.error(f"Failed to create llm_logs table: {e}")
        finally:
            if conn:
                conn.close()

    def info(self, message: str):
        self.logger.info(message, stacklevel=2)

    def debug(self, message: str):
        self.logger.debug(message, stacklevel=2)

    def error(self, message: str):
        self.logger.error(message, stacklevel=2)

    
    def log_llm_use(self, model_name: str, prompt: str, response: str, input_tokens: int, output_tokens: int, total_tokens: int, tool_name: str = None):
        try:
            conn = psycopg2.connect(**self.connection_params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO llm_logs (timestamp, model_name, prompt, response, input_tokens, output_tokens, total_tokens, tool_name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        datetime.now(timezone.utc), model_name, prompt, response, input_tokens, output_tokens, total_tokens, tool_name
                    ))
            
        except Exception as e:
            self.logger.error(f"Failed to log to PostgreSQL: {e}")
        finally:
            if conn:
                conn.close()

    
