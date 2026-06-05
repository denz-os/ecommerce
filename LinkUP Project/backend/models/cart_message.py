"""
models/cart.py
──────────────
Cart is stored per-user in MongoDB as a document
containing a list of product references + quantities.
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class CartItem(BaseModel):
    product_id: str
    quantity:   int = Field(default=1, ge=1)


class CartItemOut(BaseModel):
    product_id:   str
    name:         str
    price:        float
    image:        str        # first image URL
    quantity:     int
    line_total:   float      # price * quantity


class CartOut(BaseModel):
    user_id:    str
    items:      List[CartItemOut] = []
    total:      float = 0.0
    updated_at: datetime


"""
models/message.py
─────────────────
Direct messages between buyer and seller.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    receiver_id: str
    product_id:  Optional[str] = None
    body:        str = Field(min_length=1, max_length=1000)


class MessageOut(BaseModel):
    id:          str
    sender_id:   str
    receiver_id: str
    product_id:  Optional[str] = None
    body:        str
    sent_at:     datetime
    read:        bool = False