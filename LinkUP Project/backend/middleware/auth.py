"""
middleware/auth.py
──────────────────
JWT helpers + FastAPI dependency that protects routes.

Usage in any route:
    from middleware.auth import get_current_user

    @router.get("/me")
    async def me(user = Depends(get_current_user)):
        return user
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from bson import ObjectId

from config.database import get_db, settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Create token ──────────────────────────────────────────────
def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ── Verify token ──────────────────────────────────────────────
def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ── FastAPI dependency ────────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db)
):
    """
    Validates the Bearer token on protected routes.
    Returns the full user document from MongoDB.
    Raises 401 if token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = decode_token(token)
    if not user_id:
        raise credentials_exception

    try:
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise credentials_exception

    if not user:
        raise credentials_exception

    return user