from config.settings import Settings
from models.email_models import EmailParams
import os
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.text import MIMEText
from models.email_models import EmailType


settings = Settings()

base_dir = os.path.dirname(__file__)
templates_dir = os.path.join(base_dir, 'email', 'templates')

env = Environment(loader=FileSystemLoader(templates_dir))

template_map = {
    EmailType.SIGNUP: "signup.html",
    EmailType.RESET_PASSWORD: "reset-password.html",
    EmailType.PASSWORD_CHANGED: "password-changed.html"
}

def send_email_smtp(params:EmailParams):
    sender = settings.SENDER_EMAIL
    password = settings.GOOGLE_APP_PASSWORD
    template_file = template_map[params.email_type]
    if not template_file:
        raise ValueError(f"No template found for {params.email_type}")
    
    template = env.get_template(template_file)
    html_body = template.render(params.payload)

    msg = MIMEText(html_body, 'html')
    msg['Subject'] = params.subject
    msg['From'] = sender
    msg['To'] = params.to_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, [params.to_email], msg.as_string())
        return True
    except Exception as e:
        return False