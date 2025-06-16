import psycopg2
from settings import Settings
from llm_logger import log_debug
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
        self.conn = psycopg2.connect(
            **self.connection_params,
        )
        log_debug(f"Connected to database: {self.connection_params}")
            
        
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
            print("Connection closed.")

        
    def get_tables_info(self):
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

        return "\n".join(
            f"Table: {table}\nColumns: {', '.join(col for col, _ in cols)}"
            for table, cols in table_dict.items()
        )
    
    def run_sql_query(self, query: str):
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            return [dict(zip(col_names, row)) for row in rows]
