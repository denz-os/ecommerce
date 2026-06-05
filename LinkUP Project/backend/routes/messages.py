"""
routes/messages.py
──────────────────
GET  /api/messages/conversations  → list all conversations for current user
GET  /api/messages/{user_id}      → get chat thread with a specific user
POST /api/messages                → send a message (auth required)
PUT  /api/messages/{user_id}/read → mark all messages from user as read
"""

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from typing import List

from config.database import get_db
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["Messages"])


# ── SEND MESSAGE ──────────────────────────────────────────────
@router.post("/", status_code=201)
async def send_message(
    body: dict,          # { "receiver_id": "...", "body": "...", "product_id": "..." }
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    receiver_id_str = body.get("receiver_id")
    text            = (body.get("body") or "").strip()

    if not receiver_id_str:
        raise HTTPException(status_code=400, detail="receiver_id is required.")
    if not text:
        raise HTTPException(status_code=400, detail="Message body cannot be empty.")
    if len(text) > 1000:
        raise HTTPException(status_code=400, detail="Message too long (max 1000 chars).")

    try:
        receiver_oid = ObjectId(receiver_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid receiver_id.")

    receiver = await db["users"].find_one({"_id": receiver_oid})
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found.")

    if receiver_oid == current_user["_id"]:
        raise HTTPException(status_code=400, detail="You cannot message yourself.")

    product_oid = None
    if body.get("product_id"):
        try:
            product_oid = ObjectId(body["product_id"])
        except Exception:
            pass

    doc = {
        "sender_id":   current_user["_id"],
        "receiver_id": receiver_oid,
        "product_id":  product_oid,
        "body":        text,
        "sent_at":     datetime.utcnow(),
        "read":        False,
    }

    result = await db["messages"].insert_one(doc)
    doc["_id"] = result.inserted_id

    return _fmt_msg(doc)


# ── CONVERSATIONS LIST ────────────────────────────────────────
@router.get("/conversations")
async def get_conversations(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Returns one entry per unique conversation partner,
    with the last message and unread count.
    """
    me = current_user["_id"]

    pipeline = [
        # messages involving the current user
        {"$match": {"$or": [{"sender_id": me}, {"receiver_id": me}]}},

        # create a "partner" field = the other person's id
        {"$addFields": {
            "partner": {
                "$cond": [{"$eq": ["$sender_id", me]}, "$receiver_id", "$sender_id"]
            }
        }},

        # group by partner — keep latest message
        {"$sort": {"sent_at": -1}},
        {"$group": {
            "_id":          "$partner",
            "last_message": {"$first": "$body"},
            "last_time":    {"$first": "$sent_at"},
            "unread":       {
                "$sum": {
                    "$cond": [
                        {"$and": [
                            {"$eq":  ["$receiver_id", me]},
                            {"$eq":  ["$read", False]}
                        ]},
                        1, 0
                    ]
                }
            }
        }},
        {"$sort": {"last_time": -1}},
    ]

    results = await db["messages"].aggregate(pipeline).to_list(length=100)

    # Enrich with partner user info
    conversations = []
    for r in results:
        partner = await db["users"].find_one({"_id": r["_id"]})
        conversations.append({
            "partner_id":    str(r["_id"]),
            "partner_name":  partner["username"] if partner else "Unknown",
            "partner_pic":   partner.get("profile_pic") if partner else None,
            "last_message":  r["last_message"],
            "last_time":     r["last_time"].isoformat(),
            "unread":        r["unread"],
        })

    return conversations


# ── GET THREAD ────────────────────────────────────────────────
@router.get("/{user_id}")
async def get_thread(
    user_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        partner_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID.")

    me = current_user["_id"]

    cursor = db["messages"].find({
        "$or": [
            {"sender_id": me,          "receiver_id": partner_oid},
            {"sender_id": partner_oid, "receiver_id": me},
        ]
    }).sort("sent_at", 1)

    docs = await cursor.to_list(length=200)

    return [_fmt_msg(d) for d in docs]


# ── MARK READ ─────────────────────────────────────────────────
@router.put("/{user_id}/read")
async def mark_read(
    user_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        partner_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID.")

    await db["messages"].update_many(
        {"sender_id": partner_oid, "receiver_id": current_user["_id"], "read": False},
        {"$set": {"read": True}}
    )

    return {"message": "Marked as read."}


# ── HELPER ────────────────────────────────────────────────────
def _fmt_msg(doc: dict) -> dict:
    return {
        "id":          str(doc["_id"]),
        "sender_id":   str(doc["sender_id"]),
        "receiver_id": str(doc["receiver_id"]),
        "product_id":  str(doc["product_id"]) if doc.get("product_id") else None,
        "body":        doc["body"],
        "sent_at":     doc["sent_at"].isoformat(),
        "read":        doc.get("read", False),
    }