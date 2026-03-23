import bcrypt
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

from . import repository


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt. Returns the hash as a string."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency. Returns {"id": int, "username": str} or raises/redirects.

    For API routes (/api/*): raises HTTPException(401).
    For HTML routes: returns RedirectResponse to /login.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return _handle_unauthenticated(request)

    user = repository.get_user_by_id(user_id)
    if not user:
        request.session.clear()
        return _handle_unauthenticated(request)

    return user


def _handle_unauthenticated(request: Request):
    """Raise 401 for API routes, redirect for HTML routes."""
    if request.url.path.startswith("/api"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    raise HTTPException(status_code=302, detail="Not authenticated",
                        headers={"Location": "/login"})
