from settings import Settings
from user_repository import UserRepository

if __name__ == "__main__":
    settings = Settings()
    user_repo = UserRepository(
        settings.DB_HOST, 
        settings.DB_PORT, 
        settings.DB_USER, 
        settings.DB_PASSWORD, 
        settings.DB_NAME
    )
    
    try:
        user_repo.connect()
        print("connected successfully")
        count = user_repo.get_user_count()
        print(f"Total users: {count}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        user_repo.close()