# Proposal: Session-Based Authentication

## Intent

The app has zero access control — every endpoint is public. Even though it runs on a Tailscale VPN, team members need individual accounts to enable per-user selections and basic access gating. This change adds session-based authentication, user management UI, and migrates selections from a shared JSON file to per-user PostgreSQL storage.

## Scope

### In Scope
- Login/logout flow with Starlette SessionMiddleware (session cookie, no max_age)
- `app` schema in PostgreSQL: `users` table + `user_selections` table
- `app/auth.py` module: password hashing (bcrypt), `get_current_user` dependency
- Login page template (`app/templates/login.html`)
- User admin UI: list, create, delete users (accessible when logged in)
- User admin page template (`app/templates/users.html`)
- Migrate `storage.py` from `selections.json` to PostgreSQL per-user storage
- Protect all existing routes with auth dependency
- Logout button + user info in header
- `scripts/create_user.py` for initial admin bootstrap
- `SECRET_KEY` in `.env`

### Out of Scope
- Password reset flow (admin deletes/recreates user)
- Role-based access control (all users equal)
- Rate limiting or brute-force protection
- OAuth/SSO integration
- Email verification

## Approach

**Starlette SessionMiddleware** with signed cookies (already in the stack via FastAPI). Login POST verifies bcrypt-hashed credentials, sets `request.session["user_id"]`. A FastAPI dependency `get_current_user` checks session on every protected route, returning 401/redirect for unauthenticated requests.

New `app` schema in the existing PostgreSQL database separates auth data from the `gold` data warehouse schema. Selections move from `selections.json` to `app.user_selections` table keyed by `user_id`.

User management is a separate page (`/users`) with create/delete forms, accessible to any authenticated user.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/auth.py` | New | Auth module: bcrypt hashing, `get_current_user` dependency |
| `app/main.py` | Modified | Add SessionMiddleware, login/logout routes, user admin routes, auth dependency on all existing routes |
| `app/repository.py` | Modified | Add user CRUD queries and per-user selection queries (`app` schema) |
| `app/storage.py` | Modified | Rewrite: JSON file ops replaced with PostgreSQL per-user queries |
| `app/services.py` | Modified | Pass `user_id` to selection operations |
| `app/templates/login.html` | New | Login page |
| `app/templates/users.html` | New | User management page |
| `app/templates/index.html` | Modified | Logout button, user info in header |
| `app/static/app.js` | Modified | Handle 401 redirects, pass user context to selection API calls |
| `scripts/create_user.py` | New | CLI bootstrap script for first user |
| `requirements.txt` | Modified | Add `bcrypt`, `itsdangerous` |
| `.env` | Modified | Add `SECRET_KEY` |
| `selections.json` | Removed | Replaced by `app.user_selections` table |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| SECRET_KEY leak enables session forgery | Low | Strong random key in `.env`, `.env` is gitignored |
| Migration loses existing selections | Med | One-time migration script imports `selections.json` into DB for a default user |
| No brute-force protection | Low | App is VPN-only, small team; acceptable risk |
| DB schema conflict with `app` name | Low | Verify no existing `app` schema before CREATE |

## Rollback Plan

1. Remove SessionMiddleware from `main.py`, remove auth dependency from routes
2. Revert `storage.py` to JSON-based implementation (git revert)
3. Restore `selections.json` from backup/git
4. Drop `app` schema (`DROP SCHEMA app CASCADE`)
5. Remove `bcrypt`, `itsdangerous` from `requirements.txt`

## Dependencies

- `bcrypt` — password hashing
- `itsdangerous` — cookie signing (already a Starlette dependency, but pin explicitly)

## Success Criteria

- [ ] Unauthenticated requests to `/` and all `/api/*` redirect to `/login`
- [ ] Login with valid credentials sets session cookie and redirects to `/`
- [ ] Logout clears session and redirects to `/login`
- [ ] Cookie has no `max_age` (expires on browser close)
- [ ] Each user sees only their own saved selections
- [ ] User admin page allows creating and deleting users
- [ ] `scripts/create_user.py` creates the first user from CLI
- [ ] Existing app functionality (preview, export, filters) works unchanged after login
