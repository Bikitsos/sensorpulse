# ================================
# SensorPulse API - Authentication
# ================================

from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import get_db
from services import UserService
from schemas import TokenData, GoogleUser

# Security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, email: str) -> tuple[str, int]:
    """Create JWT access token."""
    expires_delta = timedelta(minutes=settings.jwt_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return encoded_jwt, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        exp = payload.get("exp")
        
        if not user_id or not email:
            return None
        
        return TokenData(
            user_id=user_id,
            email=email,
            exp=datetime.fromtimestamp(exp, tz=timezone.utc),
        )
    except JWTError:
        return None


async def get_google_user_info(access_token: str) -> Optional[GoogleUser]:
    """Fetch user info from Google using access token."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return GoogleUser(
                id=data["id"],
                email=data["email"],
                name=data.get("name"),
                picture=data.get("picture"),
            )
        except Exception:
            return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency to get the current authenticated user.
    Returns None if not authenticated (for optional auth endpoints).
    """
    if not credentials:
        return None
    
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        return None
    
    user_service = UserService(db)
    user = await user_service.get_by_id(token_data.user_id)
    
    return user


async def require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency to require authentication.
    Raises 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService(db)
    user = await user_service.get_by_id(token_data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized. Please contact administrator.",
        )
    
    return user


async def require_admin(user = Depends(require_user)):
    """
    FastAPI dependency to require admin privileges.
    For now, all allowed users have the same permissions.
    """
    # Could add admin flag to User model later
    return user
