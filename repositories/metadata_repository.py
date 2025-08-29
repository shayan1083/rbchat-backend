import psycopg2
from config.settings import Settings
from custom_logging.llm_logger import LLMLogger

settings = Settings()
logger = LLMLogger()

class MetadataRepository:
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
            logger.error(f"[MetadataRepository] Failed to connect to database: {e}")
        
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()

    def get_tables_info(self):
        #logger.info("(API) Fetching table and column info.")
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
                    where a.table_name  not in ('app_logs', 'chat_history', 'llm_logs', 'modified_files', 'uploaded_files')
                """)
                rows = cursor.fetchall()
            table_dict = {}
            for table_comment, table, column, dtype, column_comment in rows:
                table_dict.setdefault((table, table_comment), []).append((column, dtype, column_comment))
        except Exception as e:
            logger.error(f"(API) Failed to fetch table and column info: {e}")
            return " "
        
        return "\n\n".join(
            f"Table: {table} -- {table_comment}\n" + "\n".join(
                f"  - {col} ({dtype})" + (f" -- {comment}" if comment else "")
                for col, dtype, comment in cols
            )
            for (table, table_comment), cols in table_dict.items()
        )
        

    def get_database_names(self):
        #logger.info("(API) Fetching database names.")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, database_name, description, default_db FROM available_databases;
                """)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            return result
        except Exception as e:
            logger.error(f"(API) Failed to fetch database names: {e}")
            return []
        

    def get_uploaded_data(self, session_id: str) -> dict:
        #logger.info(f"(API) Fetching uploaded data for session: {session_id}") 
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT data, file_type, filename FROM uploaded_files WHERE session_id = %s ORDER BY upload_time DESC LIMIT 1",
                (session_id,)
            )
            result = cur.fetchone()
            file_dict = {}
            if result:
                file_dict = {
                    "data": result[0],  # JSON string
                    "file_type": result[1],
                    "filename": result[2],
                }
                return file_dict

            return None
        
    def insert_reset_code(self, user_id: str, reset_code: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO password_resets (user_id, reset_code, created_at, expires_at, type)
                    VALUES (%s, %s, NOW(), NOW() + INTERVAL '15 minutes', 'password_reset')
                    ON CONFLICT (user_id) 
                    DO UPDATE SET reset_code = EXCLUDED.reset_code, 
                                  created_at = EXCLUDED.created_at,
                                  expires_at = EXCLUDED.expires_at;
                """, (user_id, reset_code))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"(API) Error inserting reset code for user '{user_id}': {e}")
            return False
        
    def get_password_reset_obj(self, user_email: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, p.reset_code, p.expires_at
                    FROM password_resets p
                    INNER JOIN users u ON u.id = p.user_id
                    WHERE u.email = %s;
                """, (user_email.lower(),))
                row = cursor.fetchone()
            if not row:
                logger.error(f"(API) Cannot find password reset request code with email {user_email}")
                return None
            
            request_dict = {
                "email": row[0],
                "reset_code": row[1],
                "expires_at": row[2]
            }
            return request_dict
        except Exception as e:
            logger.error(f"(API) Error finding {user_email} in password reset table")
            return None
