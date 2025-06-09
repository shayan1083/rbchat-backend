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

    def get_items_by_brand(self, brand: str):
        with self.conn.cursor() as cursor:
            cursor.execute("""SELECT p.product_name, p.description, p.price 
                                FROM products p 
                                inner join brands b on p.brand_id = b.brand_id 
                                WHERE UPPER(b.brand_name) LIKE UPPER(%s);""", (brand,))
            return cursor.fetchall()
        
    
    def get_items_by_category(self, category: str):
        with self.conn.cursor() as cursor:
            cursor.execute("""SELECT p.product_name, p.description, p.price  
                                FROM products p
                                inner join categories c on p.category_id = c.category_id
                                WHERE UPPER(c.category_name) = UPPER(%s);""", (category,))
            return cursor.fetchall()

    def get_items_by_brand_and_category(self, brand: str, category: str):
        with self.conn.cursor() as cursor:
            cursor.execute("""SELECT p.product_name, p.description, p.price  
                                FROM products p
                                INNER JOIN brands b ON p.brand_id = b.brand_id
                                INNER JOIN categories c ON p.category_id = c.category_id
                                WHERE UPPER(b.brand_name) = UPPER(%s) AND UPPER(c.category_name) = UPPER(%s);""", (brand, category))
            return cursor.fetchall()

    def get_items_by_name(self, name: str):
        with self.conn.cursor() as cursor:
            cursor.execute("""SELECT p.product_name, p.description, p.price 
                                FROM products p 
                                WHERE UPPER(p.product_name) LIKE UPPER(%s);""", (f"%{name}%",))
            return cursor.fetchall()

        
    def count_items(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM products;")
            return cursor.fetchone()[0]
        
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
