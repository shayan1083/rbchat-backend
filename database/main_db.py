from config.settings import Settings
import psycopg2
from custom_logging.llm_logger import LLMLogger
from database.db_memory import ensure_chat_history_table_exists
from uuid import uuid4
from utils.hash import hash_password

settings = Settings()

logger = LLMLogger()

connection_params = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "dbname": settings.DB_NAME,
}

def create_tables(): 
    ensure_app_logs_exists()
    ensure_applications_table()
    ensure_roles_table() 
    ensure_users_table()
    ensure_llm_logs_table()
    ensure_chat_history_table_exists() 
    ensure_uploaded_files_table()
    ensure_modified_files_table()
    ensure_db_table()
    ensure_reset_password_table()
     

def ensure_db_table():
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS available_databases (
        id SERIAL PRIMARY KEY,
        database_name TEXT NOT NULL UNIQUE,
        description TEXT,
        default_db BOOLEAN NOT NULL DEFAULT FALSE
    );
    """

    insert_default_tables = """
        INSERT INTO available_databases (database_name, description, default_db)
        values
        ('postgres','transactions', true),
        ('test1', 'users', false)
        """
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                cur.execute(insert_default_tables)
        logger.info('(API) Ensured available_databases exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring available_databases exists: {e}')

def ensure_uploaded_files_table():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        data JSONB NOT NULL,
        upload_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
        logger.info('(API) Ensured uploaded_files exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring uploaded_files exists: {e}')

def ensure_llm_logs_table():
        try:
            conn = psycopg2.connect(**connection_params)
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
            logger.info("(API) llm_logs table ensured successfully.")
        except Exception as e:
            logger.error(f"(API) Failed to create llm_logs table: {e}")

def ensure_users_table():
    get_client_id = """
        SELECT client_id FROM application WHERE name = 'Rainbow Assistant' LIMIT 1;"""
    
    create_table_sql = """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email TEXT NOT NULL UNIQUE,
            fname TEXT,
            lname TEXT,
            role TEXT NOT NULL DEFAULT 'user' REFERENCES roles(name),
            location TEXT,
            last_login TIMESTAMPTZ,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            email_verified BOOLEAN DEFAULT FALSE,
            email_verification_date TIMESTAMPTZ,
            account_locked BOOLEAN DEFAULT FALSE,
            account_lock_date TIMESTAMPTZ,
            account_lock_retries INT DEFAULT 0,
            client_id UUID REFERENCES application(client_id) ON DELETE SET NULL
        );
    """
    password = hash_password("Mypassword!")
    create_user_sql = """
        INSERT INTO users (email, fname, lname, role, location, last_login, hashed_password, client_id)
        VALUES (
            'johndoe@example.com',
            'John',
            'Doe',
            'admin',
            'USA',
             NOW(),
            %s, 
            %s

        );"""
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(get_client_id)
                client_id = cur.fetchone()
              
                client_id = client_id[0]
                
                cur.execute(create_table_sql)
                cur.execute(create_user_sql, (password, client_id,))
        logger.info('(API) Ensured users table exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring users table exists: {e}')
    
def ensure_app_logs_exists():
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS app_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_id UUID,
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
            conn = psycopg2.connect(**connection_params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
            logger.info("(API) Ensured app_logs table exists")
        except Exception as e:
            print(f"(API) Failed to ensure app_logs exists: {e}")
        finally:
            if conn:
                conn.close()

def ensure_modified_files_table():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS modified_files (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        content BYTEA,              
        data JSONB,           
        upload_time TIMESTAMPTZ DEFAULT NOW()
    );
    """
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
        logger.info('(API) Ensured modified_files exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring modified_files table: {e}')

def ensure_roles_table():
    create_table_sql = """
        CREATE TABLE roles (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        );
    """

    insert_default_roles_sql = """
        INSERT INTO roles (name, description) VALUES
            ('user', 'Standard user with basic permissions'),
            ('admin', 'Administrator with full access')
        ON CONFLICT (name) DO NOTHING;
    """
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                cur.execute(insert_default_roles_sql)
        logger.info('(API) Ensured roles table and default roles exist')
    except Exception as e:
        logger.error(f'(API) Error ensuring roles table exists: {e}')

def ensure_applications_table():
    create_table_sql = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE TABLE IF NOT EXISTS application (
            client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            active BOOLEAN DEFAULT TRUE,
            client_secret TEXT NOT NULL,
            scope TEXT NOT NULL,
            allow_registration BOOLEAN DEFAULT TRUE
        );
    """
    id = str(uuid4())
    insert_seed_val = f"""
        INSERT INTO application 
        (name, description, created_at, updated_at, active, client_secret, scope) VALUES
        ('Rainbow Assistant', 'A versatile AI assistant for various tasks', NOW(), NOW(), TRUE, '{id}', 'all')
        ON CONFLICT (name) DO NOTHING;
    """
    
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                cur.execute(insert_seed_val)
        logger.info('(API) Ensured application table exists and inserted seed value')
    except Exception as e:
        logger.error(f'(API) Error ensuring application table exists: {e}')

def ensure_reset_password_table():
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS password_resets (
            id SERIAL PRIMARY KEY,
            user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            reset_code TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            type TEXT NOT NULL
        );
    """
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
        logger.info('(API) Ensured password_resets table exists')
    except Exception as e:
        logger.error(f'(API) Error ensuring password_resets table exists: {e}')
