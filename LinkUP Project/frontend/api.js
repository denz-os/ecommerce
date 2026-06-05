/**
 * api.js — LinkUP Frontend API Client
 * ─────────────────────────────────────
 * Drop this file next to your HTML files.
 * Every HTML page should include:
 *   <script src="api.js"></script>
 *
 * The module exposes a single `api` object with methods
 * for auth, products, cart and messages.
 *
 * Token is stored in localStorage under "linkup_token".
 * All authenticated requests send:
 *   Authorization: Bearer <token>
 */

const BASE_URL = "http://localhost:8000";   // ← change to your deployed URL in production

const api = (() => {

    // ── Token helpers ─────────────────────────────────────────
    function getToken()        { return localStorage.getItem("linkup_token"); }
    function setToken(t)       { localStorage.setItem("linkup_token", t); }
    function clearToken()      { localStorage.removeItem("linkup_token"); }
    function isLoggedIn()      { return !!getToken(); }

    // ── Base fetch wrapper ────────────────────────────────────
    async function request(method, path, body = null, isForm = false) {
        const headers = {};

        const token = getToken();
        if (token) headers["Authorization"] = "Bearer " + token;

        if (body && !isForm) headers["Content-Type"] = "application/json";

        const config = {
            method,
            headers,
            body: isForm ? body : (body ? JSON.stringify(body) : null),
        };

        const res = await fetch(BASE_URL + path, config);

        // 204 No Content has no body
        if (res.status === 204) return null;

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            // Throw the detail message from FastAPI's error response
            throw new Error(data.detail || "Something went wrong.");
        }

        return data;
    }

    // ═══════════════════════════════════════════════════════════
    // AUTH
    // ═══════════════════════════════════════════════════════════
    const auth = {

        async register(email, password, username = null) {
            const data = await request("POST", "/api/auth/register", { email, password, username });
            setToken(data.access_token);
            return data.user;
        },

        async login(email, password) {
            const data = await request("POST", "/api/auth/login", { email, password });
            setToken(data.access_token);
            localStorage.setItem("userEmail", data.user.email);
            localStorage.setItem("userName",  data.user.username);
            return data.user;
        },

        async me() {
            return await request("GET", "/api/auth/me");
        },

        logout() {
            clearToken();
            localStorage.removeItem("userEmail");
            localStorage.removeItem("userName");
            location.href = "login.html";
        },

        isLoggedIn,
    };

    // ═══════════════════════════════════════════════════════════
    // PRODUCTS
    // ═══════════════════════════════════════════════════════════
    const products = {

        async list({ search, category, minPrice, maxPrice, sortBy, order, limit, skip } = {}) {
            const params = new URLSearchParams();
            if (search)    params.set("search",    search);
            if (category)  params.set("category",  category);
            if (minPrice)  params.set("min_price", minPrice);
            if (maxPrice)  params.set("max_price", maxPrice);
            if (sortBy)    params.set("sort_by",   sortBy);
            if (order)     params.set("order",     order);
            if (limit)     params.set("limit",     limit);
            if (skip)      params.set("skip",      skip);

            const qs = params.toString();
            return await request("GET", `/api/products/${qs ? "?" + qs : ""}`);
        },

        async get(id) {
            return await request("GET", `/api/products/${id}`);
        },

        async create(productData) {
            return await request("POST", "/api/products/", productData);
        },

        async update(id, updates) {
            return await request("PUT", `/api/products/${id}`, updates);
        },

        async remove(id) {
            return await request("DELETE", `/api/products/${id}`);
        },

        async uploadImages(productId, fileList) {
            const form = new FormData();
            Array.from(fileList).forEach(f => form.append("files", f));
            return await request("POST", `/api/products/${productId}/images`, form, true);
        },
    };

    // ═══════════════════════════════════════════════════════════
    // CART
    // ═══════════════════════════════════════════════════════════
    const cart = {

        async get() {
            return await request("GET", "/api/cart/");
        },

        async add(productId, quantity = 1) {
            return await request("POST", "/api/cart/", { product_id: productId, quantity });
        },

        async remove(productId) {
            return await request("DELETE", `/api/cart/${productId}`);
        },

        async clear() {
            return await request("DELETE", "/api/cart/");
        },
    };

    // ═══════════════════════════════════════════════════════════
    // MESSAGES
    // ═══════════════════════════════════════════════════════════
    const messages = {

        async conversations() {
            return await request("GET", "/api/messages/conversations");
        },

        async thread(userId) {
            return await request("GET", `/api/messages/${userId}`);
        },

        async send(receiverId, body, productId = null) {
            return await request("POST", "/api/messages/", {
                receiver_id: receiverId,
                body,
                product_id: productId,
            });
        },

        async markRead(userId) {
            return await request("PUT", `/api/messages/${userId}/read`);
        },
    };

    // ─── Toast (reusable UI helper) ───────────────────────────
    function showToast(message, type = "info") {
        let toast = document.getElementById("toast");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "toast";
            document.body.appendChild(toast);
        }
        toast.innerText = message;
        toast.className = "show " + type;
        setTimeout(() => toast.classList.remove("show"), 3000);
    }

    // ─── Guard for protected pages ────────────────────────────
    function requireLogin(redirectTo = "login.html") {
        if (!isLoggedIn()) {
            showToast("Please log in to continue.");
            setTimeout(() => location.href = redirectTo, 1000);
            return false;
        }
        return true;
    }

    // ═══════════════════════════════════════════════════════════
    // ADMIN
    // ═══════════════════════════════════════════════════════════
    const admin = {
        async stats() {
            return await request("GET", "/api/admin/stats");
        },
        async users() {
            return await request("GET", "/api/admin/users");
        },
        async banUser(id) {
            return await request("PUT", `/api/admin/users/${id}/ban`);
        },
        async setRole(id, role) {
            return await request("PUT", `/api/admin/users/${id}/role`, { role });
        },
        async deleteUser(id) {
            return await request("DELETE", `/api/admin/users/${id}`);
        },
        async products() {
            return await request("GET", "/api/admin/products");
        },
        async deleteProduct(id) {
            return await request("DELETE", `/api/admin/products/${id}`);
        },
        async seed(email, password, username, secretKey) {
            return await request("POST", "/api/admin/seed", {
                email, password, username,
                secret_key: secretKey,
            });
        },
    };

    return { auth, products, cart, messages, admin, showToast, requireLogin, isLoggedIn };

})();