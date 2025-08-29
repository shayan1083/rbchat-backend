import logging
import psycopg2
from datetime import datetime, timezone
from utils.context import current_user_id

class PostgresHandler(logging.Handler):
    def __init__(self, connection_params):
        super().__init__()
        self.connection_params = connection_params

    def emit(self, record):
        try:
            user_id = current_user_id.get()
            conn = psycopg2.connect(**self.connection_params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO app_logs (timestamp, user_id, level, message, logger_name, module, function, line_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        datetime.now(timezone.utc),
                        user_id,
                        record.levelname,
                        record.getMessage(),
                        record.name,
                        record.module,
                        record.funcName,
                        record.lineno
                    ))
        except Exception as e:
            # fallback to console in case DB logging fails
            print(f"[PostgresHandler Error] {e}")
        finally:
            if conn:
                conn.close()