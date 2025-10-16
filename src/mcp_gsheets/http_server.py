#!/usr/bin/env python
import os
import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from sqlalchemy import text
import google.auth

from .auth import get_credentials_from_jwt, validate_jwt_token
from .server import mcp as sheets_mcp, SpreadsheetContext, request_context_var
from .db import get_db, engine, Base
from .models import User, OAuthCredential
from .exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    CredentialsNotFoundError,
    DatabaseError
)

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

class MCPAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            logger.info(f"MCP request to {request.url.path}")
            auth_header = request.headers.get("authorization")
            if auth_header:
                jwt_token = await get_jwt_from_header(auth_header)
                if jwt_token:
                    try:
                        logger.info("JWT token found, retrieving credentials")
                        creds = get_credentials_from_jwt(jwt_token)
                        logger.info("Building Google API services with user credentials")
                        sheets_service = build('sheets', 'v4', credentials=creds)
                        drive_service = build('drive', 'v3', credentials=creds)

                        context = SpreadsheetContext(
                            sheets_service=sheets_service,
                            drive_service=drive_service,
                            folder_id=None
                        )

                        # Set the context in contextvar for tool access
                        request.state.mcp_context = context
                        request_context_var.set(context)
                        logger.info("Per-request context set in contextvar")
                    except AuthenticationError as e:
                        logger.warning(f"Authentication failed: {e.message}")
                        # Let the exception handler deal with it
                else:
                    logger.warning("No JWT token in authorization header")
            else:
                logger.warning("No authorization header found")

        response = await call_next(request)

        # Clean up contextvar after request
        if request.url.path.startswith("/mcp"):
            request_context_var.set(None)

        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_app.lifespan(app):
        yield

app = FastAPI(title="MCP Google Sheets Server", lifespan=lifespan)
app.add_middleware(MCPAuthMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

# Exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning(f"Authentication error: {exc.message}")
    return JSONResponse(
        status_code=401,
        content={"error": exc.message}
    )

@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(f"Database error: {exc.message}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service temporarily unavailable"}
    )

def create_jwt_token(user_id: int, email: str) -> str:
    """
    Create a JWT token for user authentication.

    Args:
        user_id: User's database ID
        email: User's email address

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': now + timedelta(days=JWT_EXPIRATION_DAYS),
        'iat': now
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
    token = request.cookies.get("mcp_jwt_token")

    if token:
        try:
            jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return RedirectResponse(url="/dashboard")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass

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
        user.updated_at = datetime.now(timezone.utc)
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
    oauth_cred.updated_at = datetime.now(timezone.utc)

    db.commit()

    jwt_token = create_jwt_token(user.id, user.email)

    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="mcp_jwt_token",
        value=jwt_token,
        max_age=JWT_EXPIRATION_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax"
    )
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.cookies.get("mcp_jwt_token")

    if not token:
        return RedirectResponse(url="/")

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
        response = RedirectResponse(url="/")
        response.delete_cookie("mcp_jwt_token")
        return response
    except jwt.InvalidTokenError:
        response = RedirectResponse(url="/")
        response.delete_cookie("mcp_jwt_token")
        return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("mcp_jwt_token")
    return response

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
    """
    MCP tool call endpoint.

    Raises:
        AuthenticationError: If authentication fails
        HTTPException: For other errors
    """
    jwt_token = await get_jwt_from_header(authorization)

    if not jwt_token:
        raise AuthenticationError("Missing or invalid authorization token")

    # validate_jwt_token and get_credentials_from_jwt will raise typed exceptions
    try:
        payload = validate_jwt_token(jwt_token)
        creds = get_credentials_from_jwt(jwt_token)
    except AuthenticationError:
        # Re-raise authentication errors to be caught by exception handler
        raise

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
        logger.error(f"Error calling tool {tool_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies database connectivity.

    Returns:
        200: Service is healthy
        503: Service is unavailable (database connection failed)
    """
    checks = {
        "status": "ok",
        "database": "unknown"
    }

    # Check database connectivity
    try:
        # Execute a simple query to verify database connection
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = "unhealthy"
        checks["status"] = "degraded"
        return JSONResponse(
            status_code=503,
            content=checks
        )

    return checks

@app.get("/tools")
async def list_tools():
    tools_list = await sheets_mcp.list_tools()
    return {"tools": tools_list}

# Mount MCP app at root - this must be last so other routes take precedence
app.mount("/", mcp_app)

def main():
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
