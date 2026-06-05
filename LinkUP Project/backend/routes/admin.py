"""
routes/admin.py
───────────────
Admin-only routes. All require role === "admin".

GET  /api/admin/stats              → dashboard counts
GET  /api/admin/users              → list all users
PUT  /api/admin/users/{id}/ban     → toggle ban
PUT  /api/admin/users/{id}/role    → set role (user/admin)
DELETE /api/admin/users/{id}       → delete user
GET  /api/admin/products           → list all products
DELETE /api/admin/products/{id}    → delete any product
POST /api/admin/seed               → create first admin (disabled once one exists)
"""

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from config.database import get_db
from middleware.auth import require_admin, create_access_token
from passlib.context import CryptContext

router = APIRouter(prefix="/api/admin", tags=["Admin"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def fmt_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "email": doc.get("email"),
        "username": doc.get("username"),
        "role": doc.get("role", "user"),
        "is_banned": doc.get("is_banned", False),
        "created_at": doc.get("created_at", datetime.utcnow()).isoformat(),
        "profile_pic": doc.get("profile_pic"),
    }


def fmt_product(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title"),
        "price": doc.get("price"),
        "category": doc.get("category"),
        "seller_id": str(doc.get("seller_id", "")),
        "created_at": doc.get("created_at", datetime.utcnow()).isoformat(),
        "is_active": doc.get("is_active", True),
    }


# ── STATS ─────────────────────────────────────────────────────
@router.get("/stats")
async def get_stats(db=Depends(get_db), _=Depends(require_admin)):
    total_users = await db["users"].count_documents({})
    active_users = await db["users"].count_documents({"is_banned": {"$ne": True}})
    banned_users = await db["users"].count_documents({"is_banned": True})
    total_products = await db["products"].count_documents({})
    active_products = await db["products"].count_documents({"is_active": {"$ne": False}})
    admins = await db["users"].count_documents({"role": "admin"})

    return {
        "total_users": total_users,
        "active_users": active_users,
        "banned_users": banned_users,
        "total_products": total_products,
        "active_products": active_products,
        "admins": admins,
    }


# ── LIST USERS ────────────────────────────────────────────────
@router.get("/users")
async def list_users(db=Depends(get_db), _=Depends(require_admin)):
    cursor = db["users"].find({}).sort("created_at", -1)
    users = []
    async for doc in cursor:
        users.append(fmt_user(doc))
    return users


# ── BAN / UNBAN ───────────────────────────────────────────────
@router.put("/users/{user_id}/ban")
async def toggle_ban(user_id: str, db=Depends(get_db), admin=Depends(require_admin)):
    if user_id == str(admin["_id"]):
        raise HTTPException(status_code=400, detail="You cannot ban yourself.")

    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_status = not user.get("is_banned", False)
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_banned": new_status}}
    )
    return {"is_banned": new_status, "message": "User banned." if new_status else "User unbanned."}


# ── CHANGE ROLE ───────────────────────────────────────────────
@router.put("/users/{user_id}/role")
async def set_role(user_id: str, body: dict, db=Depends(get_db), admin=Depends(require_admin)):
    role = body.get("role")
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'.")

    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role}}
    )
    return {"message": f"Role updated to {role}."}


# ── DELETE USER ───────────────────────────────────────────────
@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db=Depends(get_db), admin=Depends(require_admin)):
    if user_id == str(admin["_id"]):
        raise HTTPException(status_code=400, detail="You cannot delete yourself.")

    result = await db["users"].delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")

    return {"message": "User deleted."}


# ── LIST ALL PRODUCTS ─────────────────────────────────────────
@router.get("/products")
async def list_products(db=Depends(get_db), _=Depends(require_admin)):
    cursor = db["products"].find({}).sort("created_at", -1)
    products = []
    async for doc in cursor:
        products.append(fmt_product(doc))
    return products


# ── DELETE ANY PRODUCT ────────────────────────────────────────
@router.delete("/products/{product_id}")
async def delete_product(product_id: str, db=Depends(get_db), _=Depends(require_admin)):
    result = await db["products"].delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found.")
    return {"message": "Product deleted."}


# ── SEED FIRST ADMIN ──────────────────────────────────────────
@router.post("/seed")
async def seed_admin(body: dict, db=Depends(get_db)):
    """
    Creates the first admin account.
    Disabled automatically once any admin exists.
    """
    secret = body.get("secret_key")
    if secret != "LINKUP_SEED_2025":
        raise HTTPException(status_code=403, detail="Invalid seed key.")

    existing_admin = await db["users"].find_one({"role": "admin"})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists. Seed disabled.")

    email = body.get("email")
    password = body.get("password")
    username = body.get("username", "Admin")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required.")

    existing = await db["users"].find_one({"email": email})
    if existing:
        # Promote existing user to admin
        await db["users"].update_one(
            {"email": email},
            {"$set": {"role": "admin"}}
        )
        return {"message": f"{email} promoted to admin."}

    doc = {
        "email": email,
        "username": username,
        "password_hash": pwd_ctx.hash(password),
        "role": "admin",
        "is_banned": False,
        "created_at": datetime.utcnow(),
    }
    await db["users"].insert_one(doc)
    return {"message": f"Admin account created for {email}."}