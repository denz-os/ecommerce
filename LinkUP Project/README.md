# LinkUP Backend — Setup Guide

**Stack:** Python · FastAPI · MongoDB · Docker

---

## Folder structure

```
linkup-backend/
├── main.py                  ← FastAPI app entry point
├── Dockerfile               ← builds the Python API image
├── docker-compose.yml       ← starts API + MongoDB + Mongo Express
├── requirements.txt         ← Python dependencies
├── .env                     ← environment variables (edit before running)
│
├── config/
│   └── database.py          ← async MongoDB connection (Motor)
│
├── middleware/
│   └── auth.py              ← JWT creation + protected route dependency
│
├── models/
│   ├── user.py              ← User Pydantic schemas
│   ├── product.py           ← Product Pydantic schemas
│   └── cart_message.py      ← Cart + Message schemas
│
├── routes/
│   ├── auth.py              ← /api/auth/*
│   ├── products.py          ← /api/products/*
│   ├── cart.py              ← /api/cart/*
│   └── messages.py          ← /api/messages/*
│
└── api.js                   ← Frontend JS client (copy next to your HTML files)
```

---

## Quick start (5 steps)

### 1 — Edit `.env`

Open `.env` and change at minimum:

```
MONGO_USER=linkup_admin
MONGO_PASS=your_secure_password     ← change this
JWT_SECRET=run_python_below_to_generate_one
```

Generate a JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2 — Build and start all containers

```bash
cd linkup-backend
docker compose up --build
```

First run downloads images and builds the Python container (~2 min).
Subsequent starts take a few seconds.

### 3 — Check everything is running

| Service          | URL                          | Notes                        |
|------------------|------------------------------|------------------------------|
| API              | http://localhost:8000        | Health check                 |
| Swagger UI       | http://localhost:8000/docs   | Interactive API docs         |
| ReDoc            | http://localhost:8000/redoc  | Alternative docs             |
| Mongo Express    | http://localhost:8081        | Visual DB browser (admin/admin123) |

### 4 — Connect your HTML frontend

Copy `api.js` into your front-end folder (next to your HTML files).

Add to the `<head>` of every HTML page:
```html
<script src="api.js"></script>
```

### 5 — Replace localStorage calls with real API calls

#### Login (`login.html`)
```javascript
// Replace your existing login() function with:
async function login() {
    const email = document.getElementById("loginEmail").value;
    const pass  = document.getElementById("loginPass").value;
    try {
        await api.auth.login(email, pass);
        location.href = "index.html";
    } catch (err) {
        document.getElementById("loginError").innerText = "⚠️ " + err.message;
    }
}
```

#### Register (`register.html`)
```javascript
async function register() {
    const email = document.getElementById("email").value;
    const pass  = document.getElementById("password").value;
    try {
        await api.auth.register(email, pass);
        location.href = "index.html";
    } catch (err) {
        document.getElementById("registerError").innerText = "⚠️ " + err.message;
    }
}
```

#### Load products (`products.html`)
```javascript
async function loadProducts(filters = {}) {
    const list = await api.products.list(filters);
    renderProducts(list, "productList");
}

// Call on page load:
loadProducts();

// With filters:
loadProducts({ category: "electronics", maxPrice: 5000 });
```

#### Add to cart
```javascript
async function addToCart(productId) {
    if (!api.requireLogin()) return;
    try {
        await api.cart.add(productId);
        api.showToast("Added to cart 🛒");
    } catch (err) {
        api.showToast(err.message, "error");
    }
}
```

#### Sell a product (`sell.html`)
```javascript
async function submitProduct() {
    if (!api.requireLogin()) return;

    // Step 1: create the product record
    const product = await api.products.create({
        name:        document.getElementById("name").value,
        price:       parseFloat(document.getElementById("price").value),
        description: document.getElementById("desc").value,
        category:    document.getElementById("category").value,
        condition:   document.getElementById("condition").value,
        location:    document.getElementById("location").value,
    });

    // Step 2: upload images if any
    const files = document.getElementById("imageUpload").files;
    if (files.length > 0) {
        await api.products.uploadImages(product.id, files);
    }

    api.showToast("Product listed successfully! 🎉");
    location.href = "products.html";
}
```

#### Protect pages that need login
```javascript
// Add this near the top of account.html, sell.html, cart.html scripts:
if (!api.requireLogin()) {
    // Redirects to login.html automatically
}
```

---

## API Reference

### Auth
| Method | Endpoint            | Body                              | Auth |
|--------|---------------------|-----------------------------------|------|
| POST   | /api/auth/register  | `{email, password, username?}`    | ✗    |
| POST   | /api/auth/login     | `{email, password}`               | ✗    |
| GET    | /api/auth/me        | —                                 | ✓    |
| PUT    | /api/auth/me        | `{username?, profile_pic?}`       | ✓    |

### Products
| Method | Endpoint                          | Notes                      | Auth |
|--------|-----------------------------------|----------------------------|------|
| GET    | /api/products/                    | ?search= ?category= ?min_price= ?max_price= ?sort_by= ?order= | ✗ |
| GET    | /api/products/{id}                | Single product             | ✗    |
| POST   | /api/products/                    | Create listing             | ✓    |
| PUT    | /api/products/{id}                | Update own listing         | ✓    |
| DELETE | /api/products/{id}                | Delete own listing         | ✓    |
| POST   | /api/products/{id}/images         | Upload images (multipart)  | ✓    |

### Cart
| Method | Endpoint              | Body                          | Auth |
|--------|-----------------------|-------------------------------|------|
| GET    | /api/cart/            | —                             | ✓    |
| POST   | /api/cart/            | `{product_id, quantity?}`     | ✓    |
| DELETE | /api/cart/{product_id}| —                             | ✓    |
| DELETE | /api/cart/            | Clear all                     | ✓    |

### Messages
| Method | Endpoint                       | Auth |
|--------|--------------------------------|------|
| GET    | /api/messages/conversations    | ✓    |
| GET    | /api/messages/{user_id}        | ✓    |
| POST   | /api/messages/                 | ✓    |
| PUT    | /api/messages/{user_id}/read   | ✓    |

---

## MongoDB Collections

| Collection | Purpose                          |
|------------|----------------------------------|
| `users`    | User accounts                    |
| `products` | Product listings                 |
| `carts`    | One cart doc per user            |
| `messages` | Direct messages between users    |

MongoDB creates these automatically when the first document is inserted — no manual schema creation needed.

---

## Useful Docker commands

```bash
# Start everything
docker compose up

# Start in background
docker compose up -d

# Stop everything
docker compose down

# View API logs
docker compose logs -f api

# Rebuild after changing requirements.txt
docker compose up --build

# Open a shell inside the API container
docker compose exec api bash

# Wipe the database volume (fresh start)
docker compose down -v
```

---

## Production checklist

- [ ] Change `MONGO_PASS` to a strong password in `.env`
- [ ] Generate a proper `JWT_SECRET` (32+ random hex chars)
- [ ] Set `allow_origins` in `main.py` to your actual frontend domain
- [ ] Put the API behind HTTPS (use Nginx or a cloud load balancer)
- [ ] Store uploaded images in cloud storage (S3, Cloudinary) instead of the container filesystem