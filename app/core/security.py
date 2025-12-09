from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
from email_validator import validate_email, EmailNotValidError
import re

def generate_token(email: str) -> str:
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='magic-link')

def verify_token(token: str, max_age: int = 86400) -> str:
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='magic-link', max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None

def validate_email_domain(email: str, allowed_domains) -> bool:
    try:
        valid = validate_email(email)
        email_normalized = valid.email
        domain = email_normalized.split('@')[1].lower()
        if isinstance(allowed_domains, str):
            allowed_domains = [allowed_domains]
        return domain in [d.strip().lower() for d in allowed_domains]
    except EmailNotValidError:
        return False

def sanitize_input(text: str) -> str:
    if not text:
        return ''
    text = text.strip()
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    return text[:5000]
