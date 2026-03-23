# Auth Specification

## Purpose

Session-based authentication using Starlette SessionMiddleware with bcrypt password hashing. Protects all routes behind login.

## Requirements

### Requirement: Session Middleware

The system MUST add Starlette `SessionMiddleware` to the FastAPI app with a `SECRET_KEY` from environment. The session cookie MUST NOT set `max_age` (expires on browser close). The cookie MUST use `httponly` flag.

#### Scenario: App starts with valid SECRET_KEY

- GIVEN the `.env` file contains a `SECRET_KEY` value
- WHEN the FastAPI application starts
- THEN SessionMiddleware is registered with that key
- AND session cookies are signed but have no `max_age`

#### Scenario: App starts without SECRET_KEY

- GIVEN the `.env` file does NOT contain `SECRET_KEY`
- WHEN the FastAPI application starts
- THEN the app MUST raise an error at startup

### Requirement: Login Endpoint

The system MUST provide `POST /login` accepting `username` and `password` form fields. On success, it MUST set `request.session["user_id"]` and redirect to `/`. On failure, it MUST re-render the login page with an error message.

#### Scenario: Valid credentials

- GIVEN a user with username "ana" and a valid password exists in `app.users`
- WHEN a POST to `/login` is made with username "ana" and the correct password
- THEN `request.session["user_id"]` is set to the user's ID
- AND the response redirects to `/`

#### Scenario: Invalid password

- GIVEN a user with username "ana" exists
- WHEN a POST to `/login` is made with username "ana" and a wrong password
- THEN the session is NOT set
- AND the login page is re-rendered with an error message

#### Scenario: Non-existent user

- GIVEN no user with username "ghost" exists
- WHEN a POST to `/login` is made with username "ghost"
- THEN the login page is re-rendered with the same generic error message (no user enumeration)

### Requirement: Logout Endpoint

The system MUST provide `POST /logout` that clears the session and redirects to `/login`.

#### Scenario: Authenticated user logs out

- GIVEN a user is logged in with a valid session
- WHEN a POST to `/logout` is made
- THEN `request.session` is cleared
- AND the response redirects to `/login`

### Requirement: Auth Dependency

The system MUST provide a FastAPI dependency `get_current_user` that checks `request.session["user_id"]`. Protected HTML routes MUST redirect to `/login`. Protected API routes MUST return 401 JSON.

#### Scenario: Authenticated request to HTML route

- GIVEN a request with a valid session containing `user_id`
- WHEN `GET /` is requested
- THEN the dependency resolves the user and the page renders normally

#### Scenario: Unauthenticated request to HTML route

- GIVEN a request with no session or expired session
- WHEN `GET /` is requested
- THEN the response redirects to `/login`

#### Scenario: Unauthenticated request to API route

- GIVEN a request with no valid session
- WHEN any `/api/*` endpoint is requested
- THEN the response is 401 JSON `{"detail": "Not authenticated"}`

### Requirement: Password Hashing

The system MUST use bcrypt to hash passwords. Plaintext passwords MUST NOT be stored.

#### Scenario: Password verification

- GIVEN a stored bcrypt hash for password "secret123"
- WHEN the system verifies "secret123" against the hash
- THEN verification succeeds

#### Scenario: Wrong password verification

- GIVEN a stored bcrypt hash for password "secret123"
- WHEN the system verifies "wrong" against the hash
- THEN verification fails
