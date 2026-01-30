# ================================
# SensorPulse API - Auth Routes
# ================================

from datetime import datetime, timezone
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from config import settings
from db import get_db
from services import UserService
from schemas import Token, User, UserPreferences
from auth import (
    create_access_token,
    get_google_user_info,
    require_user,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@router.get("/login")
async def login(
    redirect_uri: str = None,
):
    """
    Initiate Google OAuth login flow.
    
    Redirects to Google's consent screen. After authentication,
    Google will redirect back to /auth/callback.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth not configured",
        )
    
    # Build OAuth URL
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    
    if redirect_uri:
        # Store intended destination in state parameter
        params["state"] = redirect_uri
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    code: str = None,
    error: str = None,
    state: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.
    
    Exchanges authorization code for tokens, fetches user info,
    creates/updates user in database, and returns JWT.
    """
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth error: {error}",
        )
    
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing authorization code",
        )
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange authorization code",
            )
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")
    
    # Get user info from Google
    google_user = await get_google_user_info(access_token)
    if not google_user:
        raise HTTPException(
            status_code=400,
            detail="Failed to get user info from Google",
        )
    
    # Create or update user in database
    user_service = UserService(db)
    user = await user_service.create_or_update(
        email=google_user.email,
        name=google_user.name,
        picture=google_user.picture,
    )
    
    # Create JWT token
    jwt_token, expires_in = create_access_token(
        user_id=str(user.id),
        email=user.email,
    )
    
    # If state contains redirect URI, redirect there with token
    if state:
        redirect_url = f"{state}?token={jwt_token}"
        return RedirectResponse(url=redirect_url)
    
    # Otherwise return token directly
    return Token(
        access_token=jwt_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.get("/me", response_model=User)
async def get_me(
    user = Depends(require_user),
):
    """
    Get current authenticated user info.
    
    Requires valid JWT token.
    """
    return user


@router.post("/logout")
async def logout(
    response: Response,
    user = Depends(get_current_user),
):
    """
    Logout current user.
    
    Since we use stateless JWT, this just returns success.
    Client should discard the token.
    """
    # Could implement token blacklisting here if needed
    return {"message": "Logged out successfully"}


@router.put("/preferences", response_model=User)
async def update_preferences(
    preferences: UserPreferences,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Update user preferences (daily report settings).
    """
    user_service = UserService(db)
    updated_user = await user_service.update_preferences(
        user_id=str(user.id),
        daily_report=preferences.daily_report,
        report_time=preferences.report_time,
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    return updated_user
