# Design: Session-Based Authentication

## Technical Approach

Add Starlette SessionMiddleware with signed cookies to gate all routes behind login. Users and per-user selections stored in a new `app` PostgreSQL schema, reusing the existing `get_connection()` pattern. New `app/auth.py` module provides a FastAPI dependency for session validation. Login, user admin, and bootstrap script round out the change.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Session storage | Signed cookie (SessionMiddleware) | Redis-backed sessions, JWT | Already in Starlette stack, zero infra, sufficient for small VPN-only team |
| Password hashing | bcrypt via `bcrypt` lib | argon2, passlib | Simple, battle-tested, single-purpose lib (passlib is a wrapper we don't need) |
| Auth dependency | FastAPI `Depends(get_current_user)` returning user dict | Middleware-based auth | Follows existing pattern (endpoints receive injected deps), gives per-route control |
| DB schema | Separate `app` schema in same DB | Separate database, SQLite file | Reuses existing connection, clean separation from `gold` schema |
| User admin access | Any authenticated user can manage users | Admin role required | No roles in scope, team is small and trusted (VPN-only) |
| First user bootstrap | CLI script `scripts/create_user.py` | Auto-create on first run, env var seed | Explicit is better; auto-create risks accidental user creation on restarts |
| Selection storage | PostgreSQL `app.user_selections` | Keep JSON per-user files | Consistent with DB-first approach, enables future features (sharing, search) |
| Cookie expiry | Session cookie (no `max_age`) | Fixed TTL (e.g., 8h) | User decision — closes on browser exit, acceptable for internal tool |

## Data Flow

### Login
```
Browser POST /login (email, password)
  -> main.py login_post()
  -> auth.verify_password(plain, hash)
  -> repository.get_user_by_email(email)
  -> request.session["user_id"] = user.id
  -> redirect to /
```

### Authenticated Request
```
Browser GET /api/tables
  -> SessionMiddleware reads signed cookie
  -> get_current_user(request) checks session["user_id"]
     -> if missing: return 401 (API) or redirect /login (HTML)
     -> if present: repository.get_user_by_id(id) -> return user dict
  -> endpoint executes normally
```

### User Management
```
Browser POST /api/users (email, password)
  -> get_current_user (must be logged in)
  -> auth.hash_password(password)
  -> repository.create_user(email, hash)
  -> return success

Browser DELETE /api/users/{id}
  -> get_current_user (must be logged in, cannot delete self)
  -> repository.delete_user(id)
  -> return success
```

## Database Schema

```sql
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE app.user_selections (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    table_name  VARCHAR(255) NOT NULL,
    columns     TEXT NOT NULL,  -- JSON array stored as text
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, name)
);
```

The `columns` field stores a JSON-serialized list (e.g., `'["col_a","col_b"]'`). Parsed with `json.loads()` on read. This avoids a junction table for a simple list of strings.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/auth.py` | Create | `hash_password()`, `verify_password()`, `get_current_user()` dependency |
| `app/main.py` | Modify | Add SessionMiddleware, login/logout routes, user admin routes (`/users`, `/api/users`), inject `get_current_user` on all existing endpoints |
| `app/repository.py` | Modify | Add `ensure_app_schema()`, `get_user_by_email()`, `get_user_by_id()`, `create_user()`, `delete_user()`, `list_users()`, `get_user_selections()`, `save_user_selection()`, `delete_user_selection()` |
| `app/storage.py` | Modify | Rewrite all functions to call `repository.*` with `user_id` parameter instead of JSON file I/O |
| `app/services.py` | Modify | Pass `user_id` through to `storage.*` calls (minimal change) |
| `app/templates/login.html` | Create | Login form page (Tailwind CDN, matches existing style) |
| `app/templates/users.html` | Create | User list + create/delete forms (Tailwind CDN) |
| `app/templates/index.html` | Modify | Add user info + logout button in header, add link to `/users` |
| `app/static/app.js` | Modify | Handle 401 responses (redirect to `/login`), update selection API calls |
| `scripts/create_user.py` | Create | CLI: `python scripts/create_user.py email password` — bootstraps first user |
| `requirements.txt` | Modify | Add `bcrypt` |
| `.env` | Modify | Add `SECRET_KEY` (random 32+ char string) |

## Interfaces / Contracts

### `app/auth.py`
```python
import bcrypt
from fastapi import Request, HTTPException
from . import repository

def hash_password(password: str) -> str: ...
def verify_password(password: str, hashed: str) -> bool: ...
async def get_current_user(request: Request) -> dict:
    """FastAPI dependency. Returns {"id": int, "email": str} or raises HTTPException(401)."""
```

### New repository functions (`app/repository.py`)
```python
def ensure_app_schema() -> None:
    """CREATE SCHEMA + tables IF NOT EXISTS. Called once at startup."""

def get_user_by_email(email: str) -> dict | None:
    """Returns {"id", "email", "password_hash"} or None."""

def get_user_by_id(user_id: int) -> dict | None:
    """Returns {"id", "email", "created_at"} or None."""

def create_user(email: str, password_hash: str) -> dict: ...
def delete_user(user_id: int) -> bool: ...
def list_users() -> list[dict]: ...

def get_user_selections(user_id: int) -> dict:
    """Returns {name: {table, columns, created_at}} matching current storage.load_selections() shape."""

def save_user_selection(user_id: int, name: str, table: str, columns: list[str]) -> None: ...
def delete_user_selection(user_id: int, name: str) -> bool: ...
```

### Updated storage.py signatures
```python
def load_selections(user_id: int) -> dict: ...
def save_selection(user_id: int, name: str, table: str, columns: list[str]) -> None: ...
def delete_selection(user_id: int, name: str) -> bool: ...
```

### New endpoints in `main.py`
```python
GET  /login          -> login page (no auth required)
POST /login          -> verify credentials, set session, redirect /
POST /logout         -> clear session, redirect /login
GET  /users          -> user admin page (auth required)
GET  /api/users      -> list users JSON (auth required)
POST /api/users      -> create user {email, password} (auth required)
DELETE /api/users/{id} -> delete user (auth required, cannot delete self)
```

### SessionMiddleware config
```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    session_cookie="session",
    same_site="lax",
    https_only=False,  # Tailscale internal, no TLS termination at app level
)
```

## Migration Plan

1. **Schema creation**: `ensure_app_schema()` runs at app startup (idempotent `IF NOT EXISTS`)
2. **First user**: Run `scripts/create_user.py admin@team.com password` manually after deploy
3. **Selections migration**: One-time script `scripts/migrate_selections.py` reads `selections.json`, creates a default user if needed, inserts rows into `app.user_selections`. Run manually.
4. **Remove `selections.json`**: After migration verified, delete file and remove from git tracking
5. **Rollback**: `git revert` + `DROP SCHEMA app CASCADE` + restore `selections.json` from git

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `hash_password` / `verify_password` | Direct function calls with known inputs |
| Unit | `get_current_user` with/without session | Mock `request.session`, assert 401 or user dict |
| Integration | Login flow end-to-end | TestClient: POST /login with valid/invalid creds, check cookie + redirect |
| Integration | Protected routes return 401 without session | TestClient: GET /api/tables without cookie |
| Integration | Selection CRUD per-user isolation | Create 2 users, verify each only sees own selections |
| Manual | Browser session expires on close | Close browser, reopen, verify redirect to /login |

## Open Questions

- None. All decisions resolved via user input (cookie expiry, user management via UI, per-user selections, no roles).
