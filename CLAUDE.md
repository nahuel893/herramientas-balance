# Balance - Silver Column Selector

## Proyecto
Aplicacion web (FastAPI + Tailwind) para seleccionar columnas de tablas Silver de un Data Warehouse Medallion y exportarlas a CSV.

## Stack
- **Backend:** FastAPI (Python), psycopg2, pandas
- **Frontend:** HTML + Tailwind CSS (CDN) + vanilla JS
- **DB:** PostgreSQL (`medallion_db`) en `100.72.221.10:5432`, usuario `nahuel`
- **Schema principal:** `silver` (datos limpios y tipados)

## Estructura
```
Balance/
├── app/
│   ├── main.py          # Endpoints FastAPI
│   ├── database.py      # Conexion y queries a PostgreSQL
│   ├── static/app.js    # Logica frontend
│   └── templates/index.html  # Template principal
├── run.py               # Inicia uvicorn en 0.0.0.0:8000
├── selections.json      # Selecciones guardadas por el usuario
├── exports/             # CSVs exportados (gitignored)
├── .env                 # Credenciales DB (gitignored)
└── DB_CONTEXT.md        # Documentacion del Data Warehouse
```

## Endpoints
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Pagina principal |
| GET | `/api/tables` | Lista tablas silver |
| GET | `/api/columns/{table}` | Columnas de una tabla |
| POST | `/api/preview` | Preview 100 filas |
| POST | `/api/export` | Exportar CSV (con descarte de columnas unicas) |
| GET | `/api/download/{file}` | Descargar CSV |
| GET/POST/DELETE | `/api/selections` | CRUD selecciones guardadas |

## Features clave
- **Descarte automatico de columnas unicas:** Al exportar, se revisa cada columna del dataset completo con `nunique()`. Las columnas con 1 solo valor unico se descartan del CSV y se informa al usuario.
- **Filtro por fecha:** Soporte para rango de fechas en columnas date/timestamp.
- **Selecciones guardadas:** Se persisten en `selections.json`.

## Convenciones
- CSV exporta con separador `;` y encoding `utf-8-sig`
- Nombres de columnas se escapan con comillas dobles en SQL
- El frontend usa Tailwind via CDN (no build step)

## Data Warehouse
Arquitectura Medallion (Bronze -> Silver -> Gold). Ver `DB_CONTEXT.md` para detalle completo de tablas, columnas y estadisticas.
- **Bronze:** JSON crudo de ChessERP
- **Silver:** Datos normalizados y tipados (lo que usa esta app)
- **Gold:** Modelo dimensional (star schema)

## Git
- Repo: https://github.com/nahuel893/herramientas-balance
- Branch principal: `main`
- `.env`, `exports/`, `*.csv`, `*.xlsx` estan en `.gitignore`
