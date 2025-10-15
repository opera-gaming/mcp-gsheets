#!/usr/bin/env python
import os
import json
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from .db import get_db, engine, Base
from .models import User, OAuthCredential

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8080')
MCP_URL = os.environ.get('MCP_URL', 'http://localhost:8081/mcp/sse')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 30

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

app = FastAPI(title="MCP Google Sheets OAuth Service")

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

def create_jwt_token(user_id: int, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_flow():
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"{BASE_URL}/auth/callback"]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/auth/callback"
    )

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "base_url": BASE_URL
    })

@app.get("/auth/google")
async def auth_google():
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(url=authorization_url)

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str, db: Session = Depends(get_db)):
    flow = get_flow()
    flow.fetch_token(code=code)

    credentials = flow.credentials

    from googleapiclient.discovery import build
    oauth2_service = build('oauth2', 'v2', credentials=credentials)
    user_info = oauth2_service.userinfo().get().execute()

    google_id = user_info.get('id')
    email = user_info.get('email')
    name = user_info.get('name')

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = User(
            email=email,
            google_id=google_id,
            name=name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.email = email
        user.name = name
        user.updated_at = datetime.utcnow()
        db.commit()

    oauth_cred = db.query(OAuthCredential).filter(OAuthCredential.user_id == user.id).first()
    if not oauth_cred:
        oauth_cred = OAuthCredential(user_id=user.id)
        db.add(oauth_cred)

    oauth_cred.set_token(credentials.token)
    if credentials.refresh_token:
        oauth_cred.set_refresh_token(credentials.refresh_token)
    oauth_cred.token_uri = credentials.token_uri
    oauth_cred.client_id = credentials.client_id
    oauth_cred.client_secret = credentials.client_secret
    oauth_cred.scopes = json.dumps(credentials.scopes)
    oauth_cred.expiry = credentials.expiry
    oauth_cred.updated_at = datetime.utcnow()

    db.commit()

    jwt_token = create_jwt_token(user.id, user.email)

    return RedirectResponse(url=f"/dashboard?token={jwt_token}")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email = payload.get('email')

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "token": token,
            "email": email,
            "mcp_url": MCP_URL
        })
    except jwt.ExpiredSignatureError:
        return HTMLResponse("<h1>Token expired. Please re-authenticate.</h1>")
    except jwt.InvalidTokenError:
        return HTMLResponse("<h1>Invalid token.</h1>")

@app.get("/health")
async def health():
    return {"status": "ok"}

def main():
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
