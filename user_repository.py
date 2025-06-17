import psycopg2
from settings import Settings
from llm_logger import log_info, log_error

settings = Settings()

class UserRepository:
    def __init__(self):
        self.connection_params = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "dbname": settings.DB_NAME,
        }
        self.conn = None
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            log_info("[UserRepository] Database connection established.")
        except Exception as e:
            log_error(f"[UserRepository] Failed to connect to database: {e}")
        
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
            log_info("[UserRepository] Database connection closed.")

        
    def get_tables_info(self):
        log_info("[UserRepository] Fetching table and column info.")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name, column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                """)
                rows = cursor.fetchall()
            table_dict = {}
            for table, column, dtype in rows:
                table_dict.setdefault(table, []).append((column, dtype))
        except Exception as e:
            log_error(f"[UserRepository] Failed to fetch table and column info: {e}")
            return " "

        return "\n".join(
            f"Table: {table}\nColumns: {', '.join(col for col, _ in cols)}"
            for table, cols in table_dict.items()
        )
    
    def run_sql_query(self, query: str):
        log_info(f"[UserRepository] Executing SQL query: {query}")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
                return [dict(zip(col_names, row)) for row in rows]
        except Exception as e:
            log_error(f"[UserRepository] SQL execution failed: {e}")
            return []
