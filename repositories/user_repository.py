import psycopg2
from config.settings import Settings
from custom_logging.llm_logger import LLMLogger
from models.models import User
from utils.hash import hash_password
from models.application_models import Application


settings = Settings()
logger = LLMLogger()

class UserRepository:
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
            #logger.info("(API) Database connection established.")
        except Exception as e:
            logger.error(f"[UserRepository] Failed to connect to database: {e}")
        
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
            #logger.info("(API) Database connection closed.")

    def get_user_by_email(self, email: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, email, fname, lname, role, location, last_login, 
                               hashed_password, created_at, email_verified, 
                               email_verification_date, account_locked, account_lock_date, 
                               account_lock_retries, client_id
                    FROM users
                    WHERE email = %s ;
                """, (email.lower(),))
                row = cursor.fetchone()

            if not row:
                logger.error(f"(API) User '{email}' not found.")
                return None

            user_dict = {
                "id": row[0],
                "email": row[1],
                "fname": row[2],
                "lname": row[3],
                "role": row[4],
                "location": row[5],
                "lastLogin": row[6].isoformat() if row[6] else None,
                "hashed_password": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "email_verified": row[9],
                "email_verification_date": row[10].isoformat() if row[10] else None,
                "account_locked": row[11],
                "account_lock_date": row[12].isoformat() if row[12] else None,
                "account_lock_retries": row[13],
                "client_id": row[14]
                
            }
            return user_dict

        except Exception as e:
            logger.error(f"(API) Error fetching user '{email}': {e}")
            return None

        
    def get_application_info(self, id: str):
        logger.info('(API) Fetching application info from database')
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT name, description, created_at, updated_at, active, client_secret, scope, client_id, allow_registration
                    FROM application
                    WHERE client_id = %s;
                """, (id,))
                row = cursor.fetchone()
                if row:
                    return Application(
                        name=row[0],
                        description=row[1],
                        created_at=row[2],
                        updated_at=row[3],
                        active=row[4],
                        client_secret=row[5],
                        client_id=row[7],
                        allow_registration=row[8],
                        scope=row[6]
                    )
                else:
                    return None
        except Exception as e:
            logger.error(f"(API) Error fetching application info: {e}")
            return None

    def register_user(self, email: str, password: str, location: str = 'None', role: str = 'user', client_id: str = None):
        #logger.info(f"(API) Registering user: {username}")
        #hashed_password = hash_password(password)
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (email, hashed_password, location, role, client_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (email.lower(), password, location, role, client_id))
                user_id = cursor.fetchone()[0]
                self.conn.commit()
                return user_id
        except Exception as e:
            logger.error(f"(API) Error registering user '{email}': {e}")
            return None
    
    def increment_account_lock_retries(self, user_id: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET account_lock_retries = account_lock_retries + 1
                    WHERE id = %s;
                """, (user_id,))
                self.conn.commit()
        except Exception as e:
            logger.error(f"(API) Error incrementing account lock retries for user '{user_id}': {e}")

    def reset_account_lock_retries(self, user_id: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET account_lock_retries = 0, account_lock_date = NULL, account_locked = FALSE
                    WHERE id = %s;
                """, (user_id,))
                self.conn.commit()
        except Exception as e:
            logger.error(f"(API) Error resetting account lock retries for user '{user_id}': {e}")

    def lock_account(self, user_id: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET account_locked = TRUE,
                        account_lock_date = NOW()
                    WHERE id = %s;
                """, (user_id,))
                self.conn.commit()
        except Exception as e:
            logger.error(f"(API) Error locking account for user '{user_id}': {e}")

    def update_user_password(self, user_email: str, hashed_password: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET hashed_password = %s,
                        account_locked = FALSE,
                        account_lock_date = NULL,
                        account_lock_retries = 0
                    WHERE email = %s; 
                """, (hashed_password, user_email,))
                self.conn.commit()
        except Exception as e:
            logger.error(f"(API) Error updating password for '{user_email}': {e}")
    