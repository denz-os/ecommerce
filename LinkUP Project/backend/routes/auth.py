"""
routes/auth.py
──────────────
POST /api/auth/register   → create account, return token
POST /api/auth/login      → verify credentials, return token
GET  /api/auth/me         → return logged-in user's profile (protected)
PUT  /api/auth/me         → update username / profile pic (protected)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from bson import ObjectId
from datetime import datetime

from config.database import get_db
from middleware.auth import create_access_token, get_current_user
from models.user import UserCreate, UserLogin, UserOut, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def format_user(doc: dict) -> UserOut:
    """Convert a MongoDB user document to UserOut."""
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        username=doc.get("username"),
        profile_pic=doc.get("profile_pic"),
        created_at=doc.get("created_at", datetime.utcnow()),
    )


# ── REGISTER ─────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserCreate, db=Depends(get_db)):

    # Check duplicate email
    existing = await db["users"].find_one({"email": body.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    doc = {
        "email":        body.email,
        "username":     body.username or body.email.split("@")[0],
        "password_hash": hash_password(body.password),
        "profile_pic":  None,
        "created_at":   datetime.utcnow(),
    }

    result = await db["users"].insert_one(doc)
    doc["_id"] = result.inserted_id

    token = create_access_token(str(result.inserted_id))

    return TokenResponse(access_token=token, user=format_user(doc))


# ── LOGIN ─────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db=Depends(get_db)):

    user = await db["users"].find_one({"email": body.email})

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token(str(user["_id"]))

    return TokenResponse(access_token=token, user=format_user(user))


# ── ME (GET) ──────────────────────────────────────────────────
@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return format_user(current_user)


# ── ME (UPDATE) ───────────────────────────────────────────────
@router.put("/me", response_model=UserOut)
async def update_me(
    body: dict,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    allowed = {"username", "profile_pic"}
    updates = {k: v for k, v in body.items() if k in allowed}

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": updates}
    )

    updated = await db["users"].find_one({"_id": current_user["_id"]})
    return format_user(updated)

