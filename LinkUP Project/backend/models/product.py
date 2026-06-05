"""
models/product.py
─────────────────
Pydantic schemas for Product listings.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Category(str, Enum):
    electronics = "electronics"
    clothing    = "clothing"
    furniture   = "furniture"
    vehicles    = "vehicles"
    beauty      = "beauty"
    gaming      = "gaming"
    education   = "education"
    other       = "other"


class Condition(str, Enum):
    new         = "Brand New"
    excellent   = "Used - Excellent"
    good        = "Used - Good"
    refurbished = "Refurbished"


class ProductCreate(BaseModel):
    name:        str          = Field(min_length=2, max_length=120)
    price:       float        = Field(gt=0)
    description: Optional[str] = Field(default=None, max_length=500)
    category:    Category
    condition:   Condition    = Condition.new
    location:    Optional[str] = None


class ProductUpdate(BaseModel):
    name:        Optional[str]      = None
    price:       Optional[float]    = None
    description: Optional[str]      = None
    category:    Optional[Category] = None
    condition:   Optional[Condition]= None
    location:    Optional[str]      = None


class ProductOut(BaseModel):
    id:          str
    seller_id:   str
    seller_name: Optional[str] = None
    name:        str
    price:       float
    description: Optional[str] = None
    category:    str
    condition:   str
    location:    Optional[str] = None
    images:      List[str]     = []
    created_at:  datetime

    class Config:
        populate_by_name = True