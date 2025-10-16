import os
import jwt
import logging
from typing import Optional
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import User, OAuthCredential
from .exceptions import TokenExpiredError, InvalidTokenError, CredentialsNotFoundError

logger = logging.getLogger(__name__)

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'

def validate_jwt_token(token: str) -> Optional[dict]:
    """
    Validate JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        Token payload dict or None if invalid

    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise TokenExpiredError()
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise InvalidTokenError(str(e))

def get_credentials_from_jwt(token: str) -> Optional[Credentials]:
    """
    Get Google credentials from JWT token.

    Args:
        token: JWT token string

    Returns:
        Google Credentials object or None

    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid
        CredentialsNotFoundError: If user credentials not found
    """
    try:
        payload = validate_jwt_token(token)
    except (TokenExpiredError, InvalidTokenError):
        # Re-raise authentication errors
        raise

    user_id = payload.get('user_id')
    if not user_id:
        logger.error("No user_id in JWT payload")
        raise InvalidTokenError("Token missing user_id")

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.credentials:
            logger.warning(f"Credentials not found for user_id: {user_id}")
            raise CredentialsNotFoundError()

        oauth_cred = user.credentials
        creds_dict = oauth_cred.to_google_credentials_dict()

        creds = Credentials(
            token=creds_dict['token'],
            refresh_token=creds_dict['refresh_token'],
            token_uri=creds_dict['token_uri'],
            client_id=creds_dict['client_id'],
            client_secret=creds_dict['client_secret'],
            scopes=creds_dict['scopes'],
            expiry=creds_dict.get('expiry')
        )

        return creds
    finally:
        db.close()

def get_user_email_from_jwt(token: str) -> Optional[str]:
    """
    Get user email from JWT token.

    Args:
        token: JWT token string

    Returns:
        User email or None

    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid
    """
    try:
        payload = validate_jwt_token(token)
    except (TokenExpiredError, InvalidTokenError):
        return None
    return payload.get('email')
