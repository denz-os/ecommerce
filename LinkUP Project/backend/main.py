"""
main.py
───────
LinkUP FastAPI backend entry point.

Start locally (outside Docker):
    uvicorn main:app --reload

Or via Docker:
    docker compose up --build

Interactive API docs:
    http://localhost:8000/docs        ← Swagger UI
    http://localhost:8000/redoc       ← ReDoc

Mongo Express (visual DB browser):
    http://localhost:8081
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.database import connect_db, close_db, settings
from routes.auth     import router as auth_router
from routes.products import router as products_router
from routes.cart     import router as cart_router
from routes.messages import router as messages_router


# ── Lifespan (replaces deprecated on_event) ───────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()      # startup
    yield
    await close_db()        # shutdown


# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title       = "LinkUP API",
    description = "Backend for the LinkUP marketplace. Buy. Sell. Connect.",
    version     = "1.0.0",
    lifespan    = lifespan,
)


# ── CORS ──────────────────────────────────────────────────────
# During development allow all origins.
# In production replace "*" with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Static files (uploaded product images) ────────────────────
upload_dir = settings.UPLOAD_DIR
os.makedirs(upload_dir, exist_ok=True)

app.mount(
    "/static/uploads",
    StaticFiles(directory=upload_dir),
    name="uploads"
)


# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(messages_router)


# ── Health check ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status":  "LinkUP API is running ✅",
        "version": "1.0.0",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}