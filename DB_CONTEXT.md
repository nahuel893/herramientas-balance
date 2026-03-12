# Contexto del Data Warehouse - Medallion ETL

## Resumen del Proyecto

Data Warehouse con **arquitectura Medallion** (Bronze → Silver → Gold) que extrae datos de ChessERP (distribución comercial) y los transforma para análisis.

**Base de datos:** `medallion_db` (PostgreSQL)
**Usuario:** `nahuel`
**Host:** `localhost:5432`

## Arquitectura de Capas

```
Bronze (Raw)     →     Silver (Clean)     →     Gold (Analytics)
─────────────────────────────────────────────────────────────────
Datos crudos JSON      Datos normalizados      Modelo dimensional
Sin transformación     Tipados y limpios       Star Schema
```

## Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| Rango de datos | 2022-01-03 a 2026-02-20 |
| Sucursales | 14 |
| Clientes | 15,945 |
| Artículos | 3,255 |
| Vendedores | 153 (FV1: 142, FV4: 11) |
| Marcas | 98 |
| Genéricos | 27 |
| Registros fact_ventas | ~7 millones |
| Registros fact_stock | ~316,000 |

---

## CAPA GOLD (Usar para consultas analíticas)

### Tablas de Dimensiones

#### gold.dim_tiempo
Calendario de fechas (2020-2030)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| fecha | date | **PK** - Fecha |
| dia | integer | Día del mes (1-31) |
| dia_semana | integer | Día de semana (1=Lun, 7=Dom) |
| nombre_dia | varchar | Nombre del día |
| semana | integer | Semana del año |
| mes | integer | Mes (1-12) |
| nombre_mes | varchar | Nombre del mes |
| trimestre | integer | Trimestre (1-4) |
| anio | integer | Año |

---

#### gold.dim_sucursal
Sucursales/Locales de la empresa

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_sucursal | integer | **PK** - ID sucursal |
| descripcion | varchar | Nombre de la sucursal |

**Sucursales disponibles:**
| ID | Descripción |
|----|-------------|
| 1 | CASA CENTRAL |
| 3 | SUCURSAL CAFAYATE |
| 4 | SUCURSAL JOAQUIN V GONZALEZ |
| 5 | SUCURSAL METAN |
| 6 | SUCURSAL ORAN |
| 7 | SUCURSAL TARTAGAL |
| 9 | SUCURSAL PERICO |
| 10 | SUCURSAL LIBERTADOR |
| 11 | SUCURSAL MAIMARA |
| 12 | SUCURSAL HUMAHUACA |
| 13 | SUCURSAL ABRA PAMPA |
| 14 | SUCURSAL LA QUIACA |
| 15 | SUCURSAL SAN PEDRO |
| 16 | SUCURSAL GUEMES |

---

#### gold.dim_vendedor
Preventistas/Vendedores

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_vendedor | integer | **PK compuesta** - ID vendedor |
| id_sucursal | integer | **PK compuesta** - ID sucursal |
| des_vendedor | varchar | Nombre del vendedor |
| id_fuerza_ventas | integer | 1=FV1 (Preventa), 4=FV4 (Autoventa) |
| des_sucursal | varchar | Nombre de sucursal |

⚠️ **IMPORTANTE:** `id_vendedor` NO es único globalmente. Es único POR SUCURSAL.

---

#### gold.dim_cliente
Clientes

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_cliente | integer | **PK** - ID cliente |
| razon_social | varchar | Nombre legal |
| fantasia | varchar | Nombre de fantasía |
| id_sucursal | integer | Sucursal que lo atiende |
| des_sucursal | varchar | Nombre de sucursal |
| id_canal_mkt | integer | Canal de marketing |
| des_canal_mkt | varchar | Descripción canal |
| id_segmento_mkt | integer | Segmento de marketing |
| des_segmento_mkt | varchar | Descripción segmento |
| id_subcanal_mkt | integer | Subcanal de marketing |
| des_subcanal_mkt | varchar | Descripción subcanal |
| id_ruta_fv1 | integer | Ruta asignada FV1 (Preventa) |
| des_personal_fv1 | varchar | Vendedor FV1 |
| id_ruta_fv4 | integer | Ruta asignada FV4 (Autoventa) |
| des_personal_fv4 | varchar | Vendedor FV4 |
| id_ramo | integer | Ramo comercial |
| des_ramo | varchar | Descripción ramo |
| id_localidad | integer | Localidad |
| des_localidad | varchar | Nombre localidad |
| id_provincia | varchar | Provincia |
| des_provincia | varchar | Nombre provincia |
| latitud | numeric | Coordenada lat |
| longitud | numeric | Coordenada lon |
| id_lista_precio | integer | Lista de precio |
| des_lista_precio | varchar | Descripción lista |
| anulado | boolean | Cliente anulado |
| telefono_fijo | varchar | Teléfono fijo |
| telefono_movil | varchar | Teléfono móvil |

---

#### gold.dim_articulo
Artículos/Productos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_articulo | integer | **PK** - ID artículo |
| des_articulo | varchar | Descripción completa |
| marca | varchar | Marca del producto |
| generico | varchar | Categoría genérica |
| calibre | varchar | Calibre/Tamaño |
| proveedor | varchar | Proveedor |
| unidad_negocio | varchar | Unidad de negocio |
| factor_hectolitros | numeric | Factor conversión a HTL |

**Genéricos disponibles:**
ACEITES FINOS, AGUAS DANONE, AGUAS Y SODAS, ALIMENTOS, APERITIVOS, BAR, BOUTIQUE, CERVEZAS, CIGARRERIA, DISPENSER, ENERGIZANTES, ENVASES CCU, ENVASES GASEOSAS, ENVASES PALAU, EQUIPOS DE FRIO, ESPIRITUOSOS, FRATELLI B, GASEOSAS, INSUMOS, JUGOS, MARKETING, MARKETING BRANCA, SIDRAS Y LICORES, TAMBO, VINOS, VINOS CCU, VINOS FINOS

---

#### gold.dim_deposito
Depósitos/Almacenes

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_deposito | integer | **PK** - ID depósito |
| descripcion | varchar | Nombre del depósito |
| id_sucursal | integer | Sucursal asociada |
| des_sucursal | varchar | Nombre sucursal |

---

### Tablas de Hechos

#### gold.fact_ventas
Líneas de venta (~7M registros)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | integer | **PK** - ID único |
| id_cliente | integer | FK a dim_cliente |
| id_articulo | integer | FK a dim_articulo |
| id_vendedor | integer | FK a dim_vendedor (con id_sucursal) |
| id_sucursal | integer | FK a dim_sucursal |
| fecha_comprobante | date | Fecha de la venta |
| id_documento | varchar | Tipo documento |
| letra | char | Letra comprobante (A/B/C) |
| serie | integer | Serie |
| nro_doc | integer | Número documento |
| anulado | boolean | Comprobante anulado |
| cantidades_con_cargo | numeric | Cantidad con cargo |
| cantidades_sin_cargo | numeric | Cantidad bonificada |
| cantidades_total | numeric | **Cantidad total vendida** |
| subtotal_neto | numeric | Subtotal neto |
| subtotal_final | numeric | **Importe total** |
| bonificacion | numeric | Monto bonificación |
| cantidad_total_htls | numeric | Cantidad en hectolitros |

---

#### gold.fact_stock
Stock por depósito/fecha (~316K registros)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | integer | **PK** - ID único |
| date_stock | date | Fecha del stock |
| id_deposito | integer | FK a dim_deposito |
| id_articulo | integer | FK a dim_articulo |
| cant_bultos | numeric | Cantidad en bultos |
| cant_unidades | numeric | Cantidad en unidades |
| cantidad_total_htls | numeric | Cantidad en hectolitros |

---

### Tablas de Cobertura (Pre-calculadas)

#### gold.cob_preventista_marca
Cobertura por vendedor/marca (mensual)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| periodo | date | Primer día del mes |
| id_fuerza_ventas | integer | 1=FV1, 4=FV4 |
| id_vendedor | integer | ID vendedor |
| id_ruta | integer | ID ruta |
| id_sucursal | integer | ID sucursal |
| ds_sucursal | varchar | Nombre sucursal |
| marca | varchar | Marca |
| clientes_compradores | integer | Clientes únicos |
| volumen_total | numeric | Volumen vendido |

---

#### gold.cob_sucursal_marca
Cobertura por sucursal/marca (mensual)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| periodo | date | Primer día del mes |
| id_fuerza_ventas | integer | 1=FV1, 4=FV4 |
| id_sucursal | integer | ID sucursal |
| ds_sucursal | varchar | Nombre sucursal |
| marca | varchar | Marca |
| clientes_compradores | integer | Clientes únicos |
| volumen_total | numeric | Volumen vendido |

---

#### gold.cob_preventista_generico
Cobertura por vendedor/genérico (mensual)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| periodo | date | Primer día del mes |
| id_fuerza_ventas | integer | 1=FV1, 4=FV4 |
| id_vendedor | integer | ID vendedor |
| id_ruta | integer | ID ruta |
| id_sucursal | integer | ID sucursal |
| ds_sucursal | varchar | Nombre sucursal |
| generico | varchar | Genérico |
| clientes_compradores | integer | Clientes únicos |
| volumen_total | numeric | Volumen vendido |

---

## CAPA SILVER (Datos limpios intermedios)

### Tablas principales

| Tabla | Descripción |
|-------|-------------|
| silver.clients | Clientes normalizados (35 campos) |
| silver.articles | Artículos normalizados (32 campos) |
| silver.routes | Rutas de venta |
| silver.staff | Personal |
| silver.branches | Sucursales |
| silver.client_forces | Asignación cliente-fuerza |
| silver.fact_ventas | Ventas limpias |
| silver.fact_stock | Stock limpio |
| silver.deposits | Depósitos |
| silver.hectolitros | Factores de conversión |
| silver.marketing_segments | Segmentos marketing |
| silver.marketing_channels | Canales marketing |
| silver.marketing_subchannels | Subcanales marketing |
| silver.article_groupings | Agrupaciones de artículos |
| silver.sales_forces | Fuerzas de venta |

---

## CAPA BRONZE (Datos crudos)

| Tabla | Descripción |
|-------|-------------|
| bronze.raw_clients | JSON crudo de clientes |
| bronze.raw_articles | JSON crudo de artículos |
| bronze.raw_sales | JSON crudo de ventas |
| bronze.raw_stock | JSON crudo de stock |
| bronze.raw_routes | JSON crudo de rutas |
| bronze.raw_staff | JSON crudo de personal |
| bronze.raw_deposits | JSON crudo de depósitos |
| bronze.raw_hectolitros | JSON crudo de factores HTL |
| bronze.raw_marketing | JSON crudo de marketing |

---

## Fuerzas de Venta

| Fuerza | ID | Vendedores | Genéricos que vende |
|--------|-----|------------|---------------------|
| FV1 | 1 | 142 | CERVEZAS, AGUAS DANONE, VINOS CCU, SIDRAS Y LICORES |
| FV4 | 4 | 11 | FRATELLI B, VINOS, JUGOS, VINOS FINOS |

---

## ⚠️ Reglas de JOIN Importantes

### Claves Compuestas
Los IDs de vendedor, cliente y ruta **NO son únicos globalmente**. Son únicos **POR SUCURSAL**:

```sql
-- ✅ CORRECTO: JOIN con clave compuesta
SELECT *
FROM gold.fact_ventas fv
JOIN gold.dim_vendedor dv
  ON fv.id_vendedor = dv.id_vendedor
  AND fv.id_sucursal = dv.id_sucursal;

-- ❌ INCORRECTO: JOIN solo por ID
SELECT *
FROM gold.fact_ventas fv
JOIN gold.dim_vendedor dv
  ON fv.id_vendedor = dv.id_vendedor;
```

### Clientes y Rutas
```sql
-- JOIN correcto con dim_cliente
SELECT *
FROM gold.fact_ventas fv
JOIN gold.dim_cliente dc
  ON fv.id_cliente = dc.id_cliente
  AND fv.id_sucursal = dc.id_sucursal;
```

---

## Consultas de Ejemplo

### Ventas por Sucursal/Mes
```sql
SELECT
    fv.id_sucursal,
    ds.descripcion AS sucursal,
    DATE_TRUNC('month', fv.fecha_comprobante) AS mes,
    SUM(fv.cantidades_total) AS volumen,
    SUM(fv.subtotal_final) AS importe
FROM gold.fact_ventas fv
JOIN gold.dim_sucursal ds ON fv.id_sucursal = ds.id_sucursal
GROUP BY fv.id_sucursal, ds.descripcion, mes
ORDER BY mes DESC, volumen DESC;
```

### Cobertura por Marca (clientes con venta > 0)
```sql
WITH cliente_marca AS (
    SELECT
        fv.id_cliente,
        da.marca,
        SUM(fv.cantidades_total) AS total_qty
    FROM gold.fact_ventas fv
    JOIN gold.dim_articulo da ON fv.id_articulo = da.id_articulo
    WHERE fv.fecha_comprobante >= '2026-01-01'
      AND fv.fecha_comprobante < '2026-02-01'
      AND fv.id_sucursal = 1
    GROUP BY fv.id_cliente, da.marca
    HAVING SUM(fv.cantidades_total) > 0
)
SELECT
    marca,
    COUNT(DISTINCT id_cliente) AS clientes
FROM cliente_marca
GROUP BY marca
ORDER BY clientes DESC;
```

### Rutas Activas por Sucursal
```sql
SELECT 
    COUNT(DISTINCT dc.id_ruta_fv1) AS rutas_activas_fv1
FROM gold.fact_ventas fv
JOIN gold.dim_cliente dc 
    ON fv.id_cliente = dc.id_cliente 
    AND fv.id_sucursal = dc.id_sucursal
WHERE fv.id_sucursal = 1
  AND fv.fecha_comprobante >= '2026-02-01'
  AND dc.id_ruta_fv1 IS NOT NULL;
```

### Stock Actual por Marca
```sql
SELECT
    da.marca,
    SUM(fs.cant_bultos) AS bultos,
    SUM(fs.cantidad_total_htls) AS hectolitros
FROM gold.fact_stock fs
JOIN gold.dim_articulo da ON fs.id_articulo = da.id_articulo
WHERE fs.date_stock = CURRENT_DATE
GROUP BY da.marca
ORDER BY hectolitros DESC;
```

---

## Notas Importantes

1. **No filtrar por anulado**: Las ventas anuladas ya están consideradas en los totales
2. **Usar claves compuestas**: Siempre incluir `id_sucursal` en JOINs con dim_vendedor y dim_cliente
3. **Cobertura no es sumable**: Cobertura marca A + marca B ≠ cobertura total (clientes pueden comprar ambas)
4. **Periodo en cobertura**: Es el primer día del mes (ej: '2026-01-01' para enero 2026)
5. **Cantidades negativas**: Representan devoluciones, usar SUM para totales netos
