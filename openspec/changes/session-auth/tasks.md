# Tasks: Session-Based Authentication

## Phase 1: Infrastructure & Dependencies

- [x] 1.1 Add `bcrypt` to `requirements.txt`
- [x] 1.2 Add `SECRET_KEY` entry to `.env.example` (with placeholder value)
- [x] 1.3 Create `scripts/create_user.py` — CLI script: accepts `--username` and `--password` args, calls `repository.ensure_app_schema()`, hashes password with bcrypt, inserts into `app.users` via `repository.create_user()`

## Phase 2: Database & Repository Layer

- [x] 2.1 Add `ensure_app_schema()` to `app/repository.py` — executes `CREATE SCHEMA IF NOT EXISTS app`, `CREATE TABLE IF NOT EXISTS app.users` (id SERIAL PK, username VARCHAR UNIQUE, password_hash VARCHAR, created_at TIMESTAMP), `CREATE TABLE IF NOT EXISTS app.user_selections` (id SERIAL PK, user_id FK CASCADE, name VARCHAR, table_name VARCHAR, columns TEXT JSON, created_at TIMESTAMP, UNIQUE(user_id, name))
- [x] 2.2 Add user query functions to `app/repository.py`: `get_user_by_username(username) -> dict|None`, `get_user_by_id(user_id) -> dict|None`, `create_user(username, password_hash) -> dict`, `delete_user(user_id) -> bool`, `list_users() -> list[dict]`
- [x] 2.3 Add selection query functions to `app/repository.py`: `get_user_selections(user_id) -> dict`, `save_user_selection(user_id, name, table, columns) -> None` (upsert via ON CONFLICT), `delete_user_selection(user_id, name) -> bool`

## Phase 3: Auth Module

- [x] 3.1 Create `app/auth.py` with `hash_password(password) -> str` and `verify_password(password, hashed) -> bool` using bcrypt
- [x] 3.2 Add `get_current_user(request: Request) -> dict` FastAPI dependency to `app/auth.py` — reads `request.session["user_id"]`, calls `repository.get_user_by_id()`, raises `HTTPException(401)` for API routes or `HTTPException(302)` with Location header for HTML routes

## Phase 4: Storage Migration

- [x] 4.1 Rewrite `app/storage.py` — replace JSON file I/O with calls to `repository.get_user_selections(user_id)`, `repository.save_user_selection(user_id, ...)`, `repository.delete_user_selection(user_id, ...)`. All functions now require `user_id` parameter. Remove `SELECTIONS_FILE` constant.
- [x] 4.2 Update `app/services.py` — pass `user_id` through to any `storage.*` calls (currently services.py does not call storage, so verify and skip if unchanged)

## Phase 5: Backend Routes

- [x] 5.1 Add `SessionMiddleware` to `app/main.py` — import from starlette, configure with `SECRET_KEY` from env, `same_site="lax"`, `https_only=False`, no `max_age`. Fail at startup if `SECRET_KEY` is missing. Call `repository.ensure_app_schema()` at module level.
- [x] 5.2 Add auth routes to `app/main.py`: `GET /login` (render `login.html`, no auth), `POST /login` (verify credentials, set session, redirect `/`), `POST /logout` (clear session, redirect `/login`)
- [x] 5.3 Add user management routes to `app/main.py`: `GET /users` (render `users.html`, auth required), `GET /api/users` (list users JSON), `POST /api/users` (create user with username+password), `DELETE /api/users/{user_id}` (delete user, block self-deletion)
- [x] 5.4 Protect all existing endpoints in `app/main.py` — add `user = Depends(get_current_user)` to `index`, `api_tables`, `api_columns`, `api_preview`, `api_export`, `api_filter_values`, `download_file`. Update selection endpoints to pass `user["id"]` to storage functions.

## Phase 6: Frontend — Login & User Admin

- [x] 6.1 Create `app/templates/login.html` — Tailwind CDN, form with username + password fields + submit button, error message area. Style consistent with existing `index.html`.
- [x] 6.2 Create `app/templates/users.html` — Tailwind CDN, table listing users (username, created_at), create-user form (username + password), delete button per user (disabled for current user). JS: fetch `/api/users`, POST create, DELETE remove, refresh list. Uses safe DOM (createElement + textContent), 401 handling.

## Phase 7: Frontend — App Updates

- [x] 7.1 Update `app/templates/index.html` header — added logged-in username display ({{ user.username }}), "Cerrar sesion" button (POST /logout form), "Usuarios" link to /users page
- [x] 7.2 Update `app/static/app.js` — added `authFetch(url, opts)` wrapper that checks for 401 and redirects to /login. Replaced all fetch() calls in: loadTables, selectTable, loadFilterValues, onGenericoChange, previewData, exportData, loadSavedSelections, loadSelection, saveSelection.

## Phase 8: Data Migration & Cleanup

- [x] 8.1 Create `scripts/migrate_selections.py` — reads `selections.json`, accepts --user-id or --username CLI arg, inserts each selection into app.user_selections via repository functions
- [x] 8.2 Removed `selections.json` from git tracking (git rm --cached), added to `.gitignore`, removed selections.json creation from `install.bat`

## Phase 9: Smoke Test Checklist

- [ ] 9.1 Verify: app fails to start without `SECRET_KEY` in `.env`
- [ ] 9.2 Verify: `scripts/create_user.py --username admin --password test` creates user in DB
- [ ] 9.3 Verify: `GET /` redirects to `/login` when unauthenticated
- [ ] 9.4 Verify: login with valid credentials sets session, redirects to `/`
- [ ] 9.5 Verify: login with invalid credentials shows error, no session
- [ ] 9.6 Verify: all `/api/*` endpoints return 401 JSON without session
- [ ] 9.7 Verify: selections are per-user (user A cannot see user B's selections)
- [ ] 9.8 Verify: user cannot delete themselves via `DELETE /api/users/{self_id}`
- [ ] 9.9 Verify: logout clears session, redirects to `/login`
