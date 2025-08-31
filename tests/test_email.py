from service.email_service import send_email_smtp
from models.email_models import EmailParams, EmailType
from models.application_models import Application
from service.application_service import get_application_info_cached

def test_send_email_smtp():
    app = get_application_info_cached('e27f0067-7cb1-498b-9fa4-c6d4d81655fb')
    params = EmailParams(
        to_email='epicawsome94@gmail.com',
        subject='test',
        payload={
            "link": 'test_link',
        },
        email_type=EmailType.SIGNUP
    )

    assert send_email_smtp(params, app)

