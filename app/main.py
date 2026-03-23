from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from datetime import datetime

from . import repository, services, storage, auth
from .auth import get_current_user

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required. Set it in .env")

# Ensure app schema (users, selections tables) exists
repository.ensure_app_schema()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Gold Column Selector")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session",
    same_site="lax",
    https_only=False,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

# Server-side allowlist for filterable columns
FILTERABLE_COLUMNS = {
    "dim_articulo":             ["generico", "marca"],
    "fact_ventas":              ["id_sucursal", "generico", "marca"],
    "fact_ventas_contabilidad": ["id_sucursal", "generico", "marca"],
    "fact_stock":               ["id_deposito", "generico", "marca"],
    "dim_cliente":              ["id_sucursal"],
}

FACT_TABLES = {"fact_ventas", "fact_ventas_contabilidad", "fact_stock"}
ARTICULO_COLUMNS = {"generico", "marca"}


# ---------------------------------------------------------------------------
# Auth routes (no auth required)
# ---------------------------------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.post("/login")
async def login_post(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    user = repository.get_user_by_username(username)
    if user and auth.verify_password(password, user["password_hash"]):
        request.session["user_id"] = user["id"]
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(request, "login.html", {"error": "Credenciales invalidas"})


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ---------------------------------------------------------------------------
# Protected routes — existing endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "index.html", {"user": user})


@app.get("/api/tables")
async def api_tables(user: dict = Depends(get_current_user)):
    tables = repository.get_tables()
    return {"tables": tables}


@app.get("/api/columns/{table_name}")
async def api_columns(table_name: str, user: dict = Depends(get_current_user)):
    columns = repository.get_table_columns(table_name)
    return {"columns": columns}


class ColumnFilter(BaseModel):
    column: str
    values: list[str]


class PreviewRequest(BaseModel):
    table: str
    columns: list[str]
    filters: Optional[list[ColumnFilter]] = None
    date_column: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@app.post("/api/preview")
async def api_preview(req: PreviewRequest, user: dict = Depends(get_current_user)):
    if not req.columns:
        return {"error": "No columns selected"}
    return services.run_preview(
        req.table,
        req.columns,
        filters=req.filters,
        date_column=req.date_column,
        date_from=req.date_from,
        date_to=req.date_to,
    )


class ExportRequest(BaseModel):
    table: str
    columns: list[str]
    filters: Optional[list[ColumnFilter]] = None
    date_column: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@app.post("/api/export")
async def api_export(req: ExportRequest, user: dict = Depends(get_current_user)):
    if not req.columns:
        return {"error": "No columns selected"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{req.table}_{timestamp}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)

    count, exported_columns, discarded_columns = services.run_export(
        req.table,
        req.columns,
        filepath,
        req.date_column,
        req.date_from,
        req.date_to,
        filters=req.filters,
    )

    return {
        "filename": filename,
        "count": count,
        "path": filepath,
        "exported_columns": exported_columns,
        "discarded_columns": discarded_columns,
    }


@app.get("/api/filter-values/{table_name}")
async def api_filter_values(table_name: str, request: Request, user: dict = Depends(get_current_user)):
    if table_name not in FILTERABLE_COLUMNS:
        return JSONResponse({"error": f"Table '{table_name}' is not filterable"}, status_code=400)

    # Validate cascade query params against the table's allowlist
    allowed_cols = set(FILTERABLE_COLUMNS[table_name])
    cascade_params: dict[str, list[str]] = {}
    for key, val in request.query_params.items():
        if key not in allowed_cols:
            return JSONResponse(
                {"error": f"Column '{key}' is not a valid filter column for table '{table_name}'"},
                status_code=400,
            )
        # A query param may appear multiple times (multi-value); collect as list
        cascade_params[key] = request.query_params.getlist(key)

    result = {}
    for col in FILTERABLE_COLUMNS[table_name]:
        # Build parent_filters for this column: all cascade params except the column itself
        parent_filters = {k: v for k, v in cascade_params.items() if k != col}
        result[col] = repository.get_column_values(table_name, col, parent_filters)

    return result


@app.get("/api/download/{filename}")
async def download_file(filename: str, user: dict = Depends(get_current_user)):
    filepath = os.path.join(EXPORTS_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename, media_type='text/csv')
    return JSONResponse({"error": "File not found"}, status_code=404)


# ---------------------------------------------------------------------------
# Selection routes (auth required, scoped to user)
# ---------------------------------------------------------------------------

@app.get("/api/selections")
async def api_get_selections(user: dict = Depends(get_current_user)):
    selections = storage.load_selections(user["id"])
    return {"selections": selections}


class SaveSelectionRequest(BaseModel):
    name: str
    table: str
    columns: list[str]


@app.post("/api/selections")
async def api_save_selection(req: SaveSelectionRequest, user: dict = Depends(get_current_user)):
    storage.save_selection(user["id"], req.name, req.table, req.columns)
    return {"success": True}


@app.delete("/api/selections/{name}")
async def api_delete_selection(name: str, user: dict = Depends(get_current_user)):
    deleted = storage.delete_selection(user["id"], name)
    if deleted:
        return {"success": True}
    return {"error": "Selection not found"}


# ---------------------------------------------------------------------------
# User management routes (auth required)
# ---------------------------------------------------------------------------

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "users.html", {"user": user})


@app.get("/api/users")
async def api_list_users(user: dict = Depends(get_current_user)):
    users = repository.list_users()
    return {"users": users}


class CreateUserRequest(BaseModel):
    username: str
    password: str


@app.post("/api/users")
async def api_create_user(req: CreateUserRequest, user: dict = Depends(get_current_user)):
    username = req.username.strip()
    password = req.password.strip()

    if not username or not password:
        return JSONResponse({"error": "Username and password are required"}, status_code=400)

    # Check for duplicate username
    existing = repository.get_user_by_username(username)
    if existing:
        return JSONResponse({"error": "Username already exists"}, status_code=409)

    password_hash = auth.hash_password(password)
    new_user = repository.create_user(username, password_hash)
    return {"success": True, "user": new_user}


@app.delete("/api/users/{user_id}")
async def api_delete_user(user_id: int, user: dict = Depends(get_current_user)):
    # Cannot delete yourself
    if user_id == user["id"]:
        return JSONResponse({"error": "Cannot delete your own account"}, status_code=400)

    deleted = repository.delete_user(user_id)
    if not deleted:
        return JSONResponse({"error": "User not found"}, status_code=404)
    return {"success": True}
