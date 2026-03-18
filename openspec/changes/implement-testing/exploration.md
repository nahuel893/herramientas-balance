# Exploration: implement-testing

## Current State

El proyecto no tiene ningún test. La arquitectura es de 3 capas:

- `app/main.py` — rutas FastAPI, lógica mínima (construye request, delega a database.py, forma response)
- `app/database.py` — todo el acceso a datos: conexión psycopg2, queries SQL construidas con f-strings, pandas para DataFrames
- `app/templates/index.html` + `app/static/app.js` — frontend vanilla (no testeable con pytest)

Las funciones de `database.py` están acopladas a la DB real:
```python
def get_connection():
    return psycopg2.connect(host=..., port=..., dbname=..., user=..., password=...)

def export_data(table_name, columns, output_path, ...):
    conn = get_connection()   # <-- hard dependency on real DB
    df = pd.read_sql(query, conn)
    # lógica de negocio: descartar columnas con 1 valor único
    discarded = [col for col in df.columns if df[col].nunique() <= 1]
    df = df.drop(columns=discarded)
    df.to_csv(output_path, sep=';', encoding='utf-8-sig')
    return len(df), df.columns.tolist(), discarded
```

**Lógica de negocio crítica embebida**: el descarte de columnas con un único valor es la feature más importante y no tiene test.

## Affected Areas

- `app/database.py` — contiene lógica de negocio mezclada con acceso a datos; es el área más importante a cubrir
- `app/main.py` — rutas; se pueden testear con `TestClient` sin modificar
- `requirements.txt` — hay que agregar dependencias de test (`pytest`, `httpx`)
- `app/__init__.py` — sin cambios
- No hay `pyproject.toml` ni `setup.cfg`; los settings de pytest irían en `pytest.ini` o `pyproject.toml`

## Approaches

### Approach 1: pytest + FastAPI TestClient + mocks (sin DB)

Usar `fastapi.testclient.TestClient` (incluido en FastAPI) + `unittest.mock.patch` para mockear las funciones de `database.py`.

- **Pros**: rápido, sin dependencia de DB, aislado, corre en CI, cubre el contrato de la API
- **Cons**: no testea las queries SQL reales; si cambia el contrato entre main.py y database.py los tests pueden volverse incoherentes
- **Effort**: Low (2-3h)

**Cobertura posible:**
- `GET /api/tables` → retorna lista de tablas
- `GET /api/columns/{table}` → retorna columnas
- `POST /api/preview` → validación de input, shape del response
- `POST /api/export` → lógica de descarte (mockeando el DataFrame devuelto por export_data)
- `GET /api/selections` + `POST` + `DELETE` → CRUD completo (sin DB, solo filesystem)

### Approach 2: pytest + integración real con DB

Conectar a la DB real (`medallion_db`) y testear el stack completo.

- **Pros**: testea el SQL real, descubre problemas de tipos, esquemas, etc.
- **Cons**: requiere DB disponible (100.72.221.10), los tests son lentos, datos pueden variar, no apto para CI genérico
- **Effort**: Medium (requiere setup de fixtures, manejo de conexiones)

### Approach 3: refactor + unit tests puros

Extraer la lógica de negocio (descarte de columnas, construcción de queries) a funciones puras, testear esas funciones directamente con DataFrames sintéticos.

- **Pros**: cobertura máxima de la lógica de negocio, tests ultrarrápidos, mejor diseño
- **Cons**: requiere refactoring (crear un módulo `logic.py` o similar), scope más amplio
- **Effort**: Medium (refactor + tests)

### Approach 4: combinado (Approach 1 + Approach 3)

Extraer la lógica de descarte de columnas a una función pura + testearla directamente. Además, TestClient + mocks para las rutas principales.

- **Pros**: mejor coverage sin tocar DB, diseño mejorado, effort razonable
- **Cons**: requiere un pequeño refactor en database.py
- **Effort**: Medium-Low (3-5h)

## Recommendation

**Approach 4 (combinado)** es el camino correcto. La razón es simple:

La lógica de descarte de columnas únicas es el corazón del producto — si eso falla, el CSV exportado tiene datos basura. Esa lógica DEBE tener unit tests directos. Además, las rutas de la API son triviales de cubrir con TestClient + mocks.

El refactor es mínimo: extraer una función `discard_unique_columns(df)` de `database.py` a `app/logic.py`. No rompe nada.

**Stack de test sugerido:**
- `pytest` — framework de tests
- `httpx` — cliente HTTP para TestClient de FastAPI
- `pytest-cov` — cobertura (opcional pero útil)

## Risks

- El acoplamiento de `database.py` (conexión + SQL + lógica de negocio en la misma función) hace difícil testear sin mockear toda la función; el refactor parcial de Approach 4 lo resuelve
- Las rutas de selecciones (`selections.json`) usan el filesystem real — en los tests habría que usar un archivo temporal o mockear `os.path.exists` / `open`
- Si se opta por integración real (Approach 2), los datos en `silver` pueden cambiar y romper assertions hardcodeadas

## Ready for Proposal

**Sí.** La exploración está completa. El orchestrator puede lanzar `/sdd-new implement-testing` con Approach 4 como base del proposal.
