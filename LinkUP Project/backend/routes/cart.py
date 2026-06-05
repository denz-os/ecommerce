"""
routes/cart.py
──────────────
GET    /api/cart           → get current user's cart (auth required)
POST   /api/cart           → add a product to cart (auth required)
DELETE /api/cart/{product_id} → remove a product from cart (auth required)
DELETE /api/cart           → clear entire cart (auth required)
"""

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from config.database import get_db
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/cart", tags=["Cart"])


async def _build_cart_response(user_id, db) -> dict:
    """
    Fetches the cart doc, enriches each item with product details,
    and computes totals. Returns a clean dict ready for the API response.
    """
    cart_doc = await db["carts"].find_one({"user_id": user_id})

    if not cart_doc or not cart_doc.get("items"):
        return {
            "user_id":    str(user_id),
            "items":      [],
            "total":      0.0,
            "updated_at": datetime.utcnow().isoformat(),
        }

    enriched = []
    total = 0.0

    for item in cart_doc["items"]:
        product = await db["products"].find_one({"_id": item["product_id"]})

        if not product:
            # Product was deleted — skip it silently
            continue

        qty        = item.get("quantity", 1)
        line_total = float(product["price"]) * qty
        total     += line_total

        enriched.append({
            "product_id": str(item["product_id"]),
            "name":       product["name"],
            "price":      float(product["price"]),
            "image":      product["images"][0] if product.get("images") else "",
            "quantity":   qty,
            "line_total": round(line_total, 2),
        })

    return {
        "user_id":    str(user_id),
        "items":      enriched,
        "total":      round(total, 2),
        "updated_at": cart_doc.get("updated_at", datetime.utcnow()).isoformat(),
    }


# ── GET CART ──────────────────────────────────────────────────
@router.get("/")
async def get_cart(current_user=Depends(get_current_user), db=Depends(get_db)):
    return await _build_cart_response(current_user["_id"], db)


# ── ADD ITEM ──────────────────────────────────────────────────
@router.post("/")
async def add_to_cart(
    body: dict,            # { "product_id": "...", "quantity": 1 }
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    product_id_str = body.get("product_id")
    quantity       = int(body.get("quantity", 1))

    if not product_id_str:
        raise HTTPException(status_code=400, detail="product_id is required.")

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1.")

    try:
        product_oid = ObjectId(product_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID.")

    product = await db["products"].find_one({"_id": product_oid})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    user_id = current_user["_id"]

    # If item already in cart → increment quantity
    existing = await db["carts"].find_one({
        "user_id":             user_id,
        "items.product_id":    product_oid
    })

    if existing:
        await db["carts"].update_one(
            {"user_id": user_id, "items.product_id": product_oid},
            {
                "$inc": {"items.$.quantity": quantity},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    else:
        await db["carts"].update_one(
            {"user_id": user_id},
            {
                "$push": {"items": {"product_id": product_oid, "quantity": quantity}},
                "$set":  {"updated_at": datetime.utcnow()},
                "$setOnInsert": {"user_id": user_id},
            },
            upsert=True
        )

    return await _build_cart_response(user_id, db)


# ── REMOVE ITEM ───────────────────────────────────────────────
@router.delete("/{product_id}")
async def remove_from_cart(
    product_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        product_oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID.")

    user_id = current_user["_id"]

    await db["carts"].update_one(
        {"user_id": user_id},
        {
            "$pull": {"items": {"product_id": product_oid}},
            "$set":  {"updated_at": datetime.utcnow()}
        }
    )

    return await _build_cart_response(user_id, db)


# ── CLEAR CART ────────────────────────────────────────────────
@router.delete("/")
async def clear_cart(current_user=Depends(get_current_user), db=Depends(get_db)):
    await db["carts"].update_one(
        {"user_id": current_user["_id"]},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}}
    )
    return {"message": "Cart cleared."}