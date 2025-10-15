import os
import jwt
from typing import Optional
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import User, OAuthCredential

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'

def validate_jwt_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid JWT token: {e}")
        return None

def get_credentials_from_jwt(token: str) -> Optional[Credentials]:
    payload = validate_jwt_token(token)
    if not payload:
        return None

    user_id = payload.get('user_id')
    if not user_id:
        return None

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.credentials:
            return None

        oauth_cred = user.credentials
        creds_dict = oauth_cred.to_google_credentials_dict()

        creds = Credentials(
            token=creds_dict['token'],
            refresh_token=creds_dict['refresh_token'],
            token_uri=creds_dict['token_uri'],
            client_id=creds_dict['client_id'],
            client_secret=creds_dict['client_secret'],
            scopes=creds_dict['scopes']
        )

        return creds
    finally:
        db.close()

def get_user_email_from_jwt(token: str) -> Optional[str]:
    payload = validate_jwt_token(token)
    if not payload:
        return None
    return payload.get('email')
