from custom_logging.llm_logger import LLMLogger
from repositories.user_repository import UserRepository
from fastapi import HTTPException
from models.models import UserSignup
from service.email_service import send_email_smtp
from models.email_models import EmailParams, EmailType
from utils.hash import hash_password

logger = LLMLogger()

def register_user(user: UserSignup, ip: str = None):
    client = None
    with UserRepository() as repo:
            client = repo.get_application_info(user.client_id)

    if client and client.allow_registration and client.active:                  
        try:
            with UserRepository() as repo:
                if not repo.get_user_by_email(user.email):
                    logger.info(f"(API) Registering user: {user.email}")
                    print("registering user")
                    hashed_password = hash_password(user.password)
                    user_id = repo.register_user(email=user.email, password=hashed_password, location=ip, client_id=user.client_id)
                    print("inserted user in database")
                    #convert user_id into encrypted string and pass it below
                    encryptedUserID = "userid & clientid"
                    email_params = EmailParams(
                        to_email=user.email,
                        subject="Registration Successful",
                        payload={
                            "link": 'http://www.zeesystems.com/confirm-email?id=encriptedstring',
                        },
                        email_type=EmailType.SIGNUP
                    )
                    sent = send_email_smtp(email_params, client)
                    print("sent email")
                    if sent:
                        return {'message': f'User {user_id} registered successfully'}
                    else:
                        raise HTTPException(status_code=400, detail='Could not send confirmation email')
                    #send email to user
                else:
                    raise HTTPException(status_code=400, detail="User already exists")
        except HTTPException as e:
            logger.error(f"(API) Error registering user '{user.email}': {e.detail}")
            raise e   
        except Exception as e:
            logger.error(f"(API) Error registering user '{user.email}': {e}")
            return None
    else:
        logger.error(f"(API) Registration not allowed for client_id '{user.client_id}'")
        raise HTTPException(status_code=400, detail="Registration not allowed for this application")

