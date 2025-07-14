import psycopg2
from settings import Settings
from llm_logger import LLMLogger

settings = Settings()
logger = LLMLogger()

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
            logger.info("[UserRepository] Database connection established.")
        except Exception as e:
            logger.error(f"[UserRepository] Failed to connect to database: {e}")
        
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
            logger.info("[UserRepository] Database connection closed.")

        
    def get_tables_info(self):
        logger.info("[UserRepository] Fetching table and column info.")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                    b.table_comment as table_desc, 
                    a.table_name,column_name,data_type,column_desc FROM 
                    (
                    SELECT 
                        pgd.objoid ,
                        c.table_name,
                        c.column_name,
                        c.data_type,
                        pgd.description AS column_desc
                    FROM 
                        information_schema.columns c
                    LEFT JOIN 
                        pg_catalog.pg_statio_all_tables st ON st.relname = c.table_name
                    LEFT JOIN 
                        pg_catalog.pg_description pgd ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
                    WHERE 
                        c.table_schema = 'public' --and pgd.description is not null and objoid = 17053

                    ) as a

                    left join (

                    select
                        cls."oid" ,
                        cls.relname AS table_name,
                        des.description AS table_comment
                    FROM 
                        pg_catalog.pg_class cls
                    JOIN 
                        pg_catalog.pg_namespace ns ON ns.oid = cls.relnamespace
                    LEFT JOIN 
                        pg_catalog.pg_description des ON des.objoid = cls.oid AND des.objsubid = 0
                    WHERE 
                        cls.relkind = 'r'  -- Only ordinary tables
                        AND ns.nspname = 'public'
                        AND des.description IS NOT NULL
                    ) b on a.objoid  = b.oid
                """)
                rows = cursor.fetchall()
            table_dict = {}
            for table_comment, table, column, dtype, column_comment in rows:
                table_dict.setdefault((table, table_comment), []).append((column, dtype, column_comment))
        except Exception as e:
            logger.error(f"[UserRepository] Failed to fetch table and column info: {e}")
            return " "
        
        return "\n\n".join(
            f"Table: {table} -- {table_comment}\n" + "\n".join(
                f"  - {col} ({dtype})" + (f" -- {comment}" if comment else "")
                for col, dtype, comment in cols
            )
            for (table, table_comment), cols in table_dict.items()
        )
    
    def estimate_tokens(self):
        logger.info('[UserRepository] Fetching token amount of last call')
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
            logger.error(f"[User Repository] Failed to get last token call usage: {e}")
            return 0

        return row[0]
                
