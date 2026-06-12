# LinkUP Marketplace

> **School Demo Project** — but a highly functional, production-quality one.

LinkUP is a peer-to-peer e-commerce marketplace built as a school project for South Africa. While it runs entirely on `localStorage` rather than a live database, it functions exactly like a real marketplace: users can register, browse, list products, add to cart, check out via PayFast, message sellers, and manage their accounts — and admins have a fully operational control panel to manage the whole platform. 
[📄 User Manual](LinkUP_User_Manual.pdf) 

**Live demo:** [boisterous-biscotti-ebb824.netlify.app](https://boisterous-biscotti-ebb824.netlify.app)


**Admin portal:** navigate to `/admin-login.html` and use either of these credentials to manage users, products, and platform settings:

| Email | Password |
|---|---|
| `admin@linkup.com` | `Admin@2025` |
| `denzel@linkup.com` | `Denzel@2025` |

---

## What makes this demo different

Most school demo projects are static mockups. LinkUP is not. Every feature you see actually works — data persists between sessions, the admin panel enforces real access control, suspended users are genuinely blocked from logging in, and products you list on the sell page appear immediately in the marketplace. The PayFast integration uses real sandbox credentials and redirects to PayFast's actual checkout page.

---

## Features

### Buyer Experience
- Browse 35+ products across Electronics, Clothing, Furniture, Vehicles, Beauty and Books
- Advanced filter panel: category, price range (min/max), condition, delivery type, location (SA provinces), deals-only toggle
- Active filter chips — see exactly what's filtered and remove individual filters instantly
- Today's Deals strip — horizontal scroll of products under R1,000
- Grid and list view toggle
- Add to cart, adjust quantities, apply promo codes
- PayFast sandbox checkout with order confirmation
- Cash on Delivery (COD) checkout flow
- Save items to wishlist
- Rate products with a star rating

### Seller Experience
- List products with name, price, category, condition, location, delivery type, description and images
- Listings appear instantly in the marketplace and the admin panel
- Manage and delete your own listings from the account page
- Seller's products tracked separately per account

### Account & Auth
- Register, log in, log out
- Account dashboard with real data: active listings, items sold, orders, saved items
- Edit profile (name, phone, location, bio, avatar)
- Change password
- Guest mode — browse the full marketplace without an account; prompted to sign in only when trying to buy or sell

### Admin Panel (`/admin-login.html`)
- Dashboard with platform stats (users, products, orders, revenue)
- User management: view all registered users, ban/unban accounts
- Product management: view all marketplace listings, suspend/reinstate products
- Suspended products are hidden from the marketplace immediately
- Banned users are blocked from logging in and shown a clear suspension message
- "View Store" button — preview the customer-facing site as a guest without leaving the admin panel
- Global search across users and products

### Platform
- Fully responsive, mobile-first design across all pages
- Hamburger navigation on mobile
- Consistent topbar across all 12+ pages
- Real-time buyer-seller chat interface
- About page with developer information
- Deployed on Netlify

---

## Tech Stack

| Layer    | Tech                                      |
|----------|-------------------------------------------|
| Frontend | HTML, CSS, JavaScript (localStorage)      |
| Backend  | FastAPI, Python *(architecture ready)*    |
| Database | MongoDB — Motor async driver *(architecture ready)* |
| Auth     | JWT — python-jose, bcrypt — passlib *(architecture ready)* |
| Payment  | PayFast sandbox (real integration)        |
| Deploy   | Netlify (frontend)                        |

> The backend is fully architected and the API is documented below. The live demo runs on the frontend with localStorage — swapping in the real backend requires only the call changes shown in the Backend Setup section.

---

## Project Structure

```
LinkUP Project/
├── frontend/
│   ├── index.html          ← Homepage with featured products
│   ├── products.html       ← Browse + filter marketplace
│   ├── product.html        ← Single product detail page
│   ├── sell.html           ← List a product for sale
│   ├── cart.html           ← Cart + PayFast / COD checkout
│   ├── chat.html           ← Buyer-seller messaging
│   ├── account.html        ← User dashboard (listings, orders, saved)
│   ├── login.html          ← Sign in + Browse as Guest
│   ├── register.html       ← Create account
│   ├── settings.html       ← Preferences
│   ├── about.html          ← About LinkUP + developer info
│   ├── admin-login.html    ← Admin portal login
│   ├── admin.html          ← Admin control panel
│   └── style.css           ← Shared styles
└── backend/
    ├── main.py
    ├── config/             ← Database connection
    ├── models/             ← Pydantic models (user, product, cart, message)
    ├── routes/             ← API endpoints (auth, products, cart, messages)
    ├── middleware/         ← JWT auth middleware
    └── requirements.txt
```

---

## localStorage Keys (demo data layer)

| Key | Purpose |
|---|---|
| `isLoggedIn` | Auth state |
| `userEmail` / `userName` | Current user identity |
| `isGuest` | Guest browsing mode flag |
| `linkup_users` | All registered user accounts |
| `admin_products` | All marketplace products (source of truth) |
| `products` | Current seller's own listings |
| `cart` | Shopping cart items |
| `linkup_orders` | Completed order records (per buyer) |
| `linkup_saved` | Saved/wishlist items (per user) |
| `suspendedNotice` | Flag for redirected banned users |

---

## Developer

Built by **Denzel Chingodza** — [denzel.chingodza@icloud.com](mailto:denzel.chingodza@icloud.com)

---

## Backend Setup (local development)

**Stack:** Python · FastAPI · MongoDB · Docker

### Quick start

**1 — Edit `.env`**

```
MONGO_USER=linkup_admin
MONGO_PASS=your_secure_password
JWT_SECRET=run_python_below_to_generate_one
```

Generate a JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**2 — Start all containers**

```bash
cd linkup-backend
docker compose up --build
```

**3 — Verify services**

| Service       | URL                        |
|---------------|----------------------------|
| API           | http://localhost:8000      |
| Swagger UI    | http://localhost:8000/docs |
| Mongo Express | http://localhost:8081      |

**4 — Connect the frontend**

Copy `api.js` next to your HTML files and add to every page `<head>`:
```html
<script src="api.js"></script>
```

---

## API Reference

### Auth
| Method | Endpoint | Body | Auth |
|--------|----------|------|------|
| POST | /api/auth/register | `{email, password, username?}` | ✗ |
| POST | /api/auth/login | `{email, password}` | ✗ |
| GET | /api/auth/me | — | ✓ |
| PUT | /api/auth/me | `{username?, profile_pic?}` | ✓ |

### Products
| Method | Endpoint | Notes | Auth |
|--------|----------|-------|------|
| GET | /api/products/ | `?search= ?category= ?min_price= ?max_price= ?sort_by=` | ✗ |
| GET | /api/products/{id} | Single product | ✗ |
| POST | /api/products/ | Create listing | ✓ |
| PUT | /api/products/{id} | Update own listing | ✓ |
| DELETE | /api/products/{id} | Delete own listing | ✓ |
| POST | /api/products/{id}/images | Upload images (multipart) | ✓ |

### Cart
| Method | Endpoint | Body | Auth |
|--------|----------|------|------|
| GET | /api/cart/ | — | ✓ |
| POST | /api/cart/ | `{product_id, quantity?}` | ✓ |
| DELETE | /api/cart/{product_id} | — | ✓ |
| DELETE | /api/cart/ | Clear all | ✓ |

### Messages
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | /api/messages/conversations | ✓ |
| GET | /api/messages/{user_id} | ✓ |
| POST | /api/messages/ | ✓ |
| PUT | /api/messages/{user_id}/read | ✓ |

---

## Useful Docker commands

```bash
docker compose up           # Start everything
docker compose up -d        # Start in background
docker compose down         # Stop everything
docker compose logs -f api  # View API logs
docker compose up --build   # Rebuild after dependency changes
docker compose down -v      # Wipe database (fresh start)
```

---

## Production checklist

- [ ] Change `MONGO_PASS` to a strong password
- [ ] Generate a proper `JWT_SECRET` (32+ random hex chars)
- [ ] Set `allow_origins` in `main.py` to your actual frontend domain
- [ ] Put the API behind HTTPS (Nginx or cloud load balancer)
- [ ] Store uploaded images in cloud storage (S3, Cloudinary) instead of container filesystem
- [ ] Replace `localStorage` calls with the `api.js` wrappers above
