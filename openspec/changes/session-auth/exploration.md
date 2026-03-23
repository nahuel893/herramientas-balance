# Exploration: Session-Based Authentication

## Current State

The app has **zero authentication**. Every endpoint is public. The FastAPI app (`app/main.py`) serves:
- 1 HTML page (`GET /`)
- 8 API endpoints (tables, columns, preview, export, download, filter-values, selections CRUD)
- Static files (app.js)

The app runs on a Tailscale VPN (not internet-exposed), so the threat model is low. The goal is basic access control: only team members with credentials can use the tool.

**Database**: PostgreSQL `medallion_db` at `100.72.221.10:5432`, user `nahuel`. Currently only uses `gold` schema for data warehouse tables. Connection management is in `repository.py` via `get_connection()` using psycopg2 + dotenv.

**Frontend**: Server-rendered Jinja2 template (`index.html`) + vanilla JS (`app.js`). No SPA framework. Tailwind via CDN.

**Dependencies** (requirements.txt): fastapi, uvicorn, psycopg2-binary, python-dotenv, jinja2, pandas. No auth libraries currently.

## Affected Areas

- `app/main.py` — Add session middleware, login/logout endpoints, auth dependency on all existing routes
- `app/repository.py` — Add user-related queries (separate from gold schema queries)
- `app/templates/index.html` — Add logout button to header; conditionally show user info
- `app/templates/login.html` — **New file**: login page template
- `app/static/app.js` — Minimal changes (handle 401 redirects)
- `requirements.txt` — Add bcrypt, itsdangerous (or python-jose)
- `.env` — Add `SECRET_KEY` for session signing
- `run.py` — No changes needed

## Approaches

### 1. Starlette SessionMiddleware + Signed Cookies (Recommended)

FastAPI is built on Starlette, which includes `SessionMiddleware` out of the box. It uses `itsdangerous` to sign cookie data.

**How it works:**
- Add `SessionMiddleware(app, secret_key=SECRET_KEY)` to the FastAPI app
- Login POST verifies credentials, then sets `request.session["user"] = email`
- A FastAPI dependency (`get_current_user`) checks `request.session` on every protected route
- Logout clears the session
- Session data is stored IN the cookie (signed, not encrypted) — fine for just storing email/user_id

**New dependencies:** `itsdangerous` (already a Starlette dependency, but pin it), `bcrypt`

**Files to create/modify:**
- `app/auth.py` — New module: session dependency, password hashing, user queries
- `app/templates/login.html` — New template
- `app/main.py` — Add middleware, login/logout routes, apply auth dependency
- `app/repository.py` — Add `get_user_by_email()`, `create_user()` queries

**User table approach:** Create an `app` schema in medallion_db to keep auth tables separate from the data warehouse (`gold` schema). Table: `app.users (id SERIAL PK, email VARCHAR UNIQUE, password_hash VARCHAR, created_at TIMESTAMP)`.

**First user creation:** A CLI script (`scripts/create_user.py`) that prompts for email + password and inserts into `app.users`. No self-registration — admin creates users manually.

- Pros: Built into Starlette (no extra framework), simple, well-documented, minimal code, cookie-based (works perfectly with server-rendered HTML)
- Cons: Session data is in the cookie (limited size, visible but signed) — not an issue for storing just email/user_id
- Effort: Low

### 2. Server-Side Session Store (Redis/DB-backed)

Use a library like `starsessions` to store session data server-side (in PostgreSQL or Redis), with only a session ID in the cookie.

- Pros: Session data not visible in cookie, can store more data, can invalidate sessions server-side
- Cons: Extra dependency (`starsessions`), needs session table or Redis, more complexity, overkill for this use case
- Effort: Medium

### 3. JWT Tokens in httpOnly Cookies

Use `python-jose` to create JWT tokens, store them in httpOnly cookies.

- Pros: Stateless, no server-side session storage
- Cons: Can't easily invalidate tokens (need blocklist), more complex, JWT is designed for API-to-API auth not browser sessions, overkill
- Effort: Medium

## Recommendation

**Approach 1: Starlette SessionMiddleware** is the clear winner.

Reasons:
- Already built into the stack (Starlette ships with it)
- Minimal new dependencies (just `bcrypt` for password hashing; `itsdangerous` is already installed with Starlette)
- Perfect fit for server-rendered HTML with cookie-based sessions
- The team is small, runs on VPN — signed cookies are more than sufficient
- Simplest to implement and maintain

### Implementation Plan (high-level)

1. **Database**: Create `app` schema + `users` table via SQL migration script
2. **Backend auth module** (`app/auth.py`): password hashing (bcrypt), `get_current_user` dependency, user repository functions
3. **Login flow**: `GET /login` (render form), `POST /login` (verify + set session), `POST /logout` (clear session)
4. **Protect routes**: Apply `get_current_user` dependency to all existing endpoints except login
5. **Frontend**: Login page template, logout button in header, 401 handling in app.js
6. **CLI script**: `scripts/create_user.py` for initial user setup
7. **Config**: Add `SECRET_KEY` to `.env`

### Users Table Schema

```sql
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Using a separate `app` schema keeps auth concerns isolated from the data warehouse (`gold` schema). This is clean separation — the `gold` schema remains read-only for analytics, while `app` schema handles application state.

### Open Questions

1. **Session expiry**: How long should sessions last? Default Starlette sessions expire when the browser closes. We could set `max_age` on the cookie (e.g., 8 hours, 24 hours, 7 days).
2. **User management UI**: Should there be an admin page to manage users, or is the CLI script sufficient?
3. **selections.json**: Currently stored as a flat file. Should user selections be per-user (stored in DB) or remain shared? For now, keep as-is (shared).

## Risks

- **Forgotten SECRET_KEY rotation**: If the secret key leaks, all sessions can be forged. Mitigation: document that SECRET_KEY should be a strong random string in `.env`.
- **No password reset flow**: Users who forget passwords need an admin to reset via CLI. Acceptable for a small internal team.
- **Session fixation**: Starlette's SessionMiddleware handles this correctly by regenerating session on login.
- **psycopg2 connection management**: Currently opens/closes connections per query (no pooling). Adding auth queries increases connection churn slightly. Not a concern at this scale, but worth noting for future.

## Ready for Proposal

Yes — the exploration is complete. The recommended approach (Starlette SessionMiddleware + bcrypt + `app` schema) is well-understood, low-effort, and fits the existing stack perfectly. The orchestrator can proceed with `sdd-propose` to formalize the scope and implementation plan.
