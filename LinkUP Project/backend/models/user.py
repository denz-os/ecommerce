"""
models/user.py
──────────────
Pydantic schemas for User.
  - UserCreate   : what the client sends on register
  - UserLogin    : what the client sends on login
  - UserOut      : what the API returns (no password)
  - UserInDB     : the full document stored in MongoDB
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    profile_pic: Optional[str] = None
    created_at: datetime

    class Config:
        # allow reading from mongo _id field
        populate_by_name = True


class UserInDB(BaseModel):
    email: str
    username: Optional[str] = None
    password_hash: str
    profile_pic: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut