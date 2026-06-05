"""
routes/products.py
──────────────────
GET    /api/products              → list all (supports ?search= ?category= ?min_price= ?max_price=)
GET    /api/products/{id}         → single product detail
POST   /api/products              → create listing (auth required)
PUT    /api/products/{id}         → update own listing (auth required)
DELETE /api/products/{id}         → delete own listing (auth required)
POST   /api/products/{id}/images  → upload product images (auth required)
"""

import os
import uuid
import aiofiles

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from PIL import Image
import io

from config.database import get_db, settings
from middleware.auth import get_current_user
from models.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/api/products", tags=["Products"])

UPLOAD_DIR = settings.UPLOAD_DIR
MAX_BYTES  = settings.MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def fmt(doc: dict) -> dict:
    """Serialise a MongoDB product document for API response."""
    doc["id"]  = str(doc.pop("_id"))
    doc["seller_id"] = str(doc.get("seller_id", ""))
    return doc


# ── LIST ──────────────────────────────────────────────────────
@router.get("/", response_model=List[dict])
async def list_products(
    search:    Optional[str]   = Query(None),
    category:  Optional[str]   = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by:   str             = Query("created_at"),   # created_at | price
    order:     str             = Query("desc"),          # asc | desc
    limit:     int             = Query(40, le=100),
    skip:      int             = Query(0),
    db=Depends(get_db)
):
    query: dict = {}

    if search:
        # case-insensitive text search on name and description
        query["$or"] = [
            {"name":        {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    if category:
        query["category"] = category

    price_filter: dict = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
    if price_filter:
        query["price"] = price_filter

    sort_dir = -1 if order == "desc" else 1
    cursor   = db["products"].find(query).sort(sort_by, sort_dir).skip(skip).limit(limit)
    docs     = await cursor.to_list(length=limit)

    return [fmt(d) for d in docs]


# ── SINGLE ────────────────────────────────────────────────────
@router.get("/{product_id}", response_model=dict)
async def get_product(product_id: str, db=Depends(get_db)):
    try:
        doc = await db["products"].find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID.")

    if not doc:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Attach seller name
    seller = await db["users"].find_one({"_id": doc.get("seller_id")})
    if seller:
        doc["seller_name"] = seller.get("username", "Unknown")

    return fmt(doc)


# ── CREATE ────────────────────────────────────────────────────
@router.post("/", status_code=201, response_model=dict)
async def create_product(
    body: ProductCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    doc = {
        **body.model_dump(),
        "seller_id":  current_user["_id"],
        "images":     [],
        "created_at": datetime.utcnow(),
    }

    result = await db["products"].insert_one(doc)
    doc["_id"] = result.inserted_id

    return fmt(doc)


# ── UPDATE ────────────────────────────────────────────────────
@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: str,
    body: ProductUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    doc = await _get_own_product(product_id, current_user, db)

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    await db["products"].update_one({"_id": doc["_id"]}, {"$set": updates})
    updated = await db["products"].find_one({"_id": doc["_id"]})
    return fmt(updated)


# ── DELETE ────────────────────────────────────────────────────
@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    doc = await _get_own_product(product_id, current_user, db)
    await db["products"].delete_one({"_id": doc["_id"]})
    return JSONResponse(status_code=204, content={})


# ── IMAGE UPLOAD ──────────────────────────────────────────────
@router.post("/{product_id}/images", response_model=dict)
async def upload_images(
    product_id: str,
    files: List[UploadFile] = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    doc = await _get_own_product(product_id, current_user, db)

    if len(files) > 6:
        raise HTTPException(status_code=400, detail="Max 6 images per product.")

    urls = []

    for file in files:

        # Validate MIME type
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"{file.filename}: only JPEG, PNG and WebP are accepted."
            )

        raw = await file.read()

        # Validate file size
        if len(raw) > MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"{file.filename} exceeds {settings.MAX_UPLOAD_MB}MB limit."
            )

        # Resize with Pillow so large files don't bloat the server
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.thumbnail((1200, 1200))

        filename  = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(UPLOAD_DIR, filename)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)

        async with aiofiles.open(save_path, "wb") as f:
            await f.write(buf.read())

        # Public URL — served by FastAPI static files (configured in main.py)
        urls.append(f"/static/uploads/{filename}")

    # Append new URLs to existing images array
    await db["products"].update_one(
        {"_id": doc["_id"]},
        {"$push": {"images": {"$each": urls}}}
    )

    updated = await db["products"].find_one({"_id": doc["_id"]})
    return fmt(updated)


# ── HELPER ────────────────────────────────────────────────────
async def _get_own_product(product_id: str, current_user: dict, db):
    """
    Fetches the product and verifies the current user is the seller.
    Raises 404 or 403 as appropriate.
    """
    try:
        doc = await db["products"].find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID.")

    if not doc:
        raise HTTPException(status_code=404, detail="Product not found.")

    if str(doc["seller_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own listings."
        )

    return doc