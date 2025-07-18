import logging
import psycopg2
from datetime import datetime, timezone
from settings import Settings
from postgres_logging import PostgresHandler
from langchain_core.messages import HumanMessage, AIMessage 
import time
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import BaseChatMessageHistory


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
            self.logger.error(f"Failed to log to PostgreSQL: {e}", stacklevel=2)
        finally:
            if conn:
                conn.close()

    def log_on_chat_end(self, history: BaseChatMessageHistory, prompt: str, full_response, start_time, input_tokens, output_tokens, total_tokens, model: ChatOpenAI, tool_name=None):
        history.add_message(HumanMessage(content=prompt))
        history.add_message(AIMessage(content=full_response))

        self.info(f"Full Response: {full_response}")
        elapsed_time = time.perf_counter() - start_time
        self.info(f"Elapsed Time: {elapsed_time:.2f} seconds")

        token_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }

        self.info(f"Token Usage: {token_usage}")
        self.log_llm_use(
            model.model_name,
            prompt,
            full_response,
            token_usage.get("input_tokens"),
            token_usage.get("output_tokens"),
            token_usage.get("total_tokens"),
            tool_name
        )

    
