# Proposal: Migrate to Gold Schema

## Intent

Reemplazar el schema `silver` por `gold` en toda la aplicación. La app dejará de exponer tablas Silver y pasará a trabajar exclusivamente con el star schema Gold (dimensiones + hechos). No hay selector de schema — Gold es el único schema.

## Scope

### In Scope
- Reemplazar todas las referencias hardcodeadas a `silver` por `gold` en backend
- Renombrar `get_silver_tables()` → `get_tables()` en repository y su caller en main.py
- Actualizar `build_select_query()` y `fetch_data()` para usar schema `gold`
- Actualizar título/labels en UI (dejar de decir "Silver")
- Limpiar `selections.json` existente (las selecciones silver no son válidas contra gold)
- Actualizar `CLAUDE.md` para reflejar el cambio de schema

### Out of Scope
- Soporte multi-schema (se descartó)
- Paginación o streaming para tablas grandes
- Cambios en lógica de descarte de columnas o export CSV

## Approach

**Reemplazo directo de schema.** Cada ocurrencia de `"silver"` en queries SQL y nombres de funciones se reemplaza por `"gold"`. Es un cambio de string en 4 archivos. La arquitectura no cambia.

```
silver."{table_name}"  →  gold."{table_name}"
WHERE table_schema = 'silver'  →  WHERE table_schema = 'gold'
get_silver_tables()  →  get_tables()
```

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/repository.py` | Modified | 3 ocurrencias de 'silver' → 'gold'; renombrar función |
| `app/services.py` | Modified | 1 ocurrencia en `build_select_query()` |
| `app/main.py` | Modified | Actualizar llamada a `get_tables()`; actualizar labels si los hay |
| `app/templates/index.html` | Modified | Título y labels que digan "Silver" |
| `selections.json` | Reset | Vaciar o dejar como está (las selecciones silver no matchean tablas gold) |
| `CLAUDE.md` | Modified | Actualizar schema principal a `gold` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `selections.json` con selecciones silver apuntando a tablas inexistentes en gold | High | Vaciar el archivo al deployar |
| Nombres de tablas distintos entre silver y gold (ej: `clientes` vs `dim_cliente`) | High | Verificar en DB_CONTEXT.md antes de implementar |
| `fact_ventas` en gold tiene ~7M rows — export lento sin filtro de fecha | Medium | Ya existe soporte de filtro de fecha en la UI |

## Rollback Plan

`git revert` del commit. Restaurar `selections.json` desde git si es necesario.

## Dependencies

- Schema `gold` accesible con las credenciales actuales en `.env`

## Success Criteria

- [ ] `/api/tables` retorna tablas del schema `gold`
- [ ] Preview y export funcionan contra tablas gold
- [ ] No hay ninguna referencia a `silver` en el código Python
- [ ] UI no menciona "Silver" en ningún label
- [ ] `CLAUDE.md` refleja schema `gold` como schema principal
