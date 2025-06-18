import logging
import psycopg2
from datetime import datetime, timezone

class PostgresHandler(logging.Handler):
    def __init__(self, connection_params):
        super().__init__()
        self.connection_params = connection_params
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS app_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            logger_name TEXT,
            module TEXT,
            function TEXT,
            line_number INT
        );
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
        except Exception as e:
            print(f"[PostgresHandler Error] Failed to ensure table exists: {e}")
        finally:
            if conn:
                conn.close()


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