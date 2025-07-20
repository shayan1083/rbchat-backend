import logging
import psycopg2
from datetime import datetime, timezone

class PostgresHandler(logging.Handler):
    def __init__(self, connection_params):
        super().__init__()
        self.connection_params = connection_params

    def emit(self, record):
        try:
            conn = psycopg2.connect(**self.connection_params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO app_logs (timestamp, level, message, logger_name, module, function, line_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (
                        datetime.now(timezone.utc),
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