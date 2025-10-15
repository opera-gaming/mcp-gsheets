import os
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet
from .db import Base

ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    google_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    credentials = relationship("OAuthCredential", back_populates="user", uselist=False)

class OAuthCredential(Base):
    __tablename__ = 'oauth_credentials'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    encrypted_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text)
    token_uri = Column(String)
    client_id = Column(String)
    client_secret = Column(String)
    scopes = Column(Text)
    expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="credentials")

    def set_token(self, token: str):
        self.encrypted_token = fernet.encrypt(token.encode()).decode()

    def get_token(self) -> str:
        return fernet.decrypt(self.encrypted_token.encode()).decode()

    def set_refresh_token(self, refresh_token: str):
        if refresh_token:
            self.encrypted_refresh_token = fernet.encrypt(refresh_token.encode()).decode()

    def get_refresh_token(self) -> str:
        if self.encrypted_refresh_token:
            return fernet.decrypt(self.encrypted_refresh_token.encode()).decode()
        return None

    def to_google_credentials_dict(self) -> dict:
        return {
            'token': self.get_token(),
            'refresh_token': self.get_refresh_token(),
            'token_uri': self.token_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scopes': json.loads(self.scopes) if self.scopes else [],
            'expiry': self.expiry,
        }
