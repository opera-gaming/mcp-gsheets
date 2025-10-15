#!/usr/bin/env python
import os
import json
from typing import Any, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

import jwt
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
import google.auth

from .auth import get_credentials_from_jwt, validate_jwt_token
from .server import mcp as sheets_mcp
from .db import get_db, engine, Base
from .models import User, OAuthCredential

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8080')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 30

mcp_app = sheets_mcp.http_app()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_app.lifespan(app):
        yield

app = FastAPI(title="MCP Google Sheets Server", lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app.mount("/mcp", mcp_app)

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
        scopes=OAUTH_SCOPES,
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

        mcp_url = f"{BASE_URL}/mcp"

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "token": token,
            "email": email,
            "mcp_url": mcp_url
        })
    except jwt.ExpiredSignatureError:
        return HTMLResponse("<h1>Token expired. Please re-authenticate.</h1>")
    except jwt.InvalidTokenError:
        return HTMLResponse("<h1>Invalid token.</h1>")

@dataclass
class RequestContext:
    user_email: Optional[str] = None
    jwt_token: Optional[str] = None

async def get_jwt_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        mcp_auth_token = os.environ.get('MCP_AUTH_TOKEN')
        if mcp_auth_token:
            return mcp_auth_token
        return None

    if not authorization.startswith('Bearer '):
        return None

    return authorization[7:]

@app.post("/mcp/v1/call")
async def mcp_call(request: Request, authorization: Optional[str] = Header(None)):
    jwt_token = await get_jwt_from_header(authorization)

    if not jwt_token:
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")

    payload = validate_jwt_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    creds = get_credentials_from_jwt(jwt_token)
    if not creds:
        raise HTTPException(status_code=401, detail="Unable to retrieve credentials")

    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    body = await request.json()

    tool_name = body.get('tool')
    arguments = body.get('arguments', {})

    try:
        from .server import SpreadsheetContext
        from mcp.server.fastmcp import Context

        context = Context(
            request_context=type('obj', (object,), {
                'lifespan_context': SpreadsheetContext(
                    sheets_service=sheets_service,
                    drive_service=drive_service,
                    folder_id=None
                )
            })()
        )

        arguments['ctx'] = context

        result = await sheets_mcp.call_tool(tool_name, arguments)

        return JSONResponse(content={"result": result})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/tools")
async def list_tools():
    tools_list = await sheets_mcp.list_tools()
    return {"tools": tools_list}

def main():
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
