from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os
from datetime import datetime

from . import repository, services, storage

app = FastAPI(title="Gold Column Selector")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

EXPORTS_DIR = os.path.join(BASE_DIR, "exports")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/tables")
async def api_tables():
    tables = repository.get_tables()
    return {"tables": tables}


@app.get("/api/columns/{table_name}")
async def api_columns(table_name: str):
    columns = repository.get_table_columns(table_name)
    return {"columns": columns}


class PreviewRequest(BaseModel):
    table: str
    columns: list[str]


@app.post("/api/preview")
async def api_preview(req: PreviewRequest):
    if not req.columns:
        return {"error": "No columns selected"}
    return services.run_preview(req.table, req.columns)


class ExportRequest(BaseModel):
    table: str
    columns: list[str]
    date_column: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@app.post("/api/export")
async def api_export(req: ExportRequest):
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
    )

    return {
        "filename": filename,
        "count": count,
        "path": filepath,
        "exported_columns": exported_columns,
        "discarded_columns": discarded_columns,
    }


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    filepath = os.path.join(EXPORTS_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename, media_type='text/csv')
    return JSONResponse({"error": "File not found"}, status_code=404)


@app.get("/api/selections")
async def api_get_selections():
    selections = storage.load_selections()
    return {"selections": selections}


class SaveSelectionRequest(BaseModel):
    name: str
    table: str
    columns: list[str]


@app.post("/api/selections")
async def api_save_selection(req: SaveSelectionRequest):
    storage.save_selection(req.name, req.table, req.columns)
    return {"success": True}


@app.delete("/api/selections/{name}")
async def api_delete_selection(name: str):
    deleted = storage.delete_selection(name)
    if deleted:
        return {"success": True}
    return {"error": "Selection not found"}
