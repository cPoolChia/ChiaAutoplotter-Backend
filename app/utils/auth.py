import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import EmailStr, ValidationError
from app import schemas, models

import emails
from emails.template import JinjaTemplate
from jose import jwt

from app.core.config import settings


def generate_email_token(email: EmailStr, delta: timedelta) -> str:
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": str(email)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def generate_password_reset_token(email: EmailStr) -> str:
    return generate_email_token(
        email, timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    )


def generate_email_confirmation_token(email: EmailStr) -> str:
    return generate_email_token(
        email, timedelta(hours=settings.EMAIL_CONFIRM_TOKEN_EXPIRE_HOURS)
    )


def verify_email_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        payload = schemas.EmailTokenPayload(**decoded_token)
        return payload.sub
    except (jwt.JWTError, ValidationError):
        return None