from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime

from .database import get_silver_tables, get_table_columns, preview_data, export_data

app = FastAPI(title="Silver Column Selector")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

SELECTIONS_FILE = os.path.join(BASE_DIR, "selections.json")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

def load_selections():
    if os.path.exists(SELECTIONS_FILE):
        with open(SELECTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_selections(selections):
    with open(SELECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(selections, f, indent=2, ensure_ascii=False)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/tables")
async def api_tables():
    tables = get_silver_tables()
    return {"tables": tables}

@app.get("/api/columns/{table_name}")
async def api_columns(table_name: str):
    columns = get_table_columns(table_name)
    return {"columns": columns}

class PreviewRequest(BaseModel):
    table: str
    columns: list[str]

@app.post("/api/preview")
async def api_preview(req: PreviewRequest):
    if not req.columns:
        return {"error": "No columns selected"}
    df = preview_data(req.table, req.columns)
    return {
        "columns": df.columns.tolist(),
        "data": df.values.tolist(),
        "count": len(df)
    }

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

    count, exported_columns, discarded_columns = export_data(
        req.table,
        req.columns,
        filepath,
        req.date_column,
        req.date_from,
        req.date_to
    )

    return {
        "filename": filename,
        "count": count,
        "path": filepath,
        "exported_columns": exported_columns,
        "discarded_columns": discarded_columns
    }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    filepath = os.path.join(EXPORTS_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename, media_type='text/csv')
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.get("/api/selections")
async def api_get_selections():
    selections = load_selections()
    return {"selections": selections}

class SaveSelectionRequest(BaseModel):
    name: str
    table: str
    columns: list[str]

@app.post("/api/selections")
async def api_save_selection(req: SaveSelectionRequest):
    selections = load_selections()
    selections[req.name] = {
        "table": req.table,
        "columns": req.columns,
        "created_at": datetime.now().isoformat()
    }
    save_selections(selections)
    return {"success": True}

@app.delete("/api/selections/{name}")
async def api_delete_selection(name: str):
    selections = load_selections()
    if name in selections:
        del selections[name]
        save_selections(selections)
        return {"success": True}
    return {"error": "Selection not found"}
