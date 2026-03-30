let currentTable = null;
let selectedColumns = [];
let allColumns = [];

// Auth-aware fetch wrapper: redirects to /login on 401
async function authFetch(url, options) {
    const res = await fetch(url, options);
    if (res.status === 401) {
        window.location.href = '/login';
        return res;
    }
    return res;
}

// Static filter config — mirrors FILTERABLE_COLUMNS on the server
const TABLE_FILTERS = {
    "dim_articulo": [
        { col: "generico", label: "Genérico", cascades: "marca" },
        { col: "marca",    label: "Marca" }
    ],
    "fact_ventas": [
        { col: "id_sucursal", label: "Sucursal" },
        { col: "generico",    label: "Genérico", cascades: "marca" },
        { col: "marca",       label: "Marca" }
    ],
    "fact_ventas_contabilidad": [
        { col: "id_sucursal", label: "Sucursal" },
        { col: "generico",    label: "Genérico", cascades: "marca" },
        { col: "marca",       label: "Marca" }
    ],
    "fact_stock": [
        { col: "id_deposito", label: "Depósito" },
        { col: "generico",    label: "Genérico", cascades: "marca" },
        { col: "marca",       label: "Marca" }
    ],
    "dim_cliente": [
        { col: "id_sucursal", label: "Sucursal" }
    ]
};

document.addEventListener('DOMContentLoaded', () => {
    loadTables();
    loadSavedSelections();
    document.getElementById('savedSelections').addEventListener('change', loadSelection);
});

async function loadTables() {
    const res = await authFetch('/api/tables');
    const data = await res.json();
    const container = document.getElementById('tablesList');
    container.innerHTML = data.tables.map(t => `
        <div class="table-item cursor-pointer px-3 py-2 rounded text-sm" onclick="selectTable('${t}')" data-table="${t}">
            ${t}
        </div>
    `).join('');
}

async function selectTable(tableName) {
    currentTable = tableName;
    selectedColumns = [];

    document.querySelectorAll('.table-item').forEach(el => {
        el.classList.remove('active');
        if (el.dataset.table === tableName) el.classList.add('active');
    });

    document.getElementById('tableNameDisplay').textContent = tableName;

    const res = await authFetch(`/api/columns/${tableName}`);
    const data = await res.json();
    allColumns = data.columns;

    renderColumns();
    updateDateColumnOptions();

    // Load filter controls for this table
    if (tableName in TABLE_FILTERS) {
        await loadFilterValues(tableName);
    } else {
        const filterSection = document.getElementById('filterSection');
        filterSection.classList.add('hidden');
        document.getElementById('filterControls').innerHTML = '';
    }
}

// Load filter values from the server and render controls
async function loadFilterValues(table, cascadeParams = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(cascadeParams)) {
        if (Array.isArray(v)) {
            v.forEach(val => qs.append(k, val));
        } else {
            qs.append(k, v);
        }
    }
    const url = `/api/filter-values/${table}` + (qs.toString() ? '?' + qs.toString() : '');
    const res = await authFetch(url);
    if (!res.ok) return;
    const data = await res.json();
    renderFilterControls(table, data);
}

// Render checkbox lists for each filterable column
function renderFilterControls(table, valuesData) {
    const filterDefs = TABLE_FILTERS[table];
    if (!filterDefs) {
        document.getElementById('filterSection').classList.add('hidden');
        return;
    }

    const controls = document.getElementById('filterControls');
    controls.innerHTML = '';

    filterDefs.forEach(fd => {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex flex-col gap-1 min-w-40';

        const labelEl = document.createElement('label');
        labelEl.className = 'text-sm font-medium text-gray-600';
        labelEl.textContent = fd.label;

        const listEl = document.createElement('div');
        listEl.id = 'filter-' + fd.col;
        listEl.className = 'border rounded px-2 py-1 max-h-40 overflow-y-auto bg-white';
        if (fd.cascades) {
            listEl.dataset.cascades = fd.cascades;
            listEl.dataset.table = table;
        }

        fillCheckboxList(listEl, fd.col, valuesData[fd.col] || [], !!fd.cascades);

        wrapper.appendChild(labelEl);
        wrapper.appendChild(listEl);
        controls.appendChild(wrapper);
    });

    document.getElementById('filterSection').classList.remove('hidden');
}

// Sync the "Todos" checkbox state with individual item checkboxes
function syncTodosCheckbox(container) {
    const todosCheckbox = container.querySelector('input[data-todos]');
    if (!todosCheckbox) return;
    const itemCheckboxes = container.querySelectorAll('input[type=checkbox]:not([data-todos])');
    const allChecked = itemCheckboxes.length > 0 && Array.from(itemCheckboxes).every(cb => cb.checked);
    todosCheckbox.checked = allChecked;
}

// Populate a checkbox container with values (items are {value, label} objects)
function fillCheckboxList(container, colName, items, hasCascade) {
    container.innerHTML = '';
    if (items.length === 0) {
        const empty = document.createElement('span');
        empty.className = 'text-gray-400 text-xs';
        empty.textContent = 'Sin valores';
        container.appendChild(empty);
        return;
    }

    // "Todos" checkbox at the top
    const todosLabel = document.createElement('label');
    todosLabel.className = 'flex items-center gap-2 px-1 py-0.5 bg-gray-100 rounded cursor-pointer text-sm font-semibold border-b mb-1 sticky top-0';

    const todosCb = document.createElement('input');
    todosCb.type = 'checkbox';
    todosCb.dataset.todos = '1';
    todosCb.addEventListener('change', () => {
        const itemCheckboxes = container.querySelectorAll('input[type=checkbox]:not([data-todos])');
        itemCheckboxes.forEach(cb => { cb.checked = todosCb.checked; });
        if (hasCascade) onGenericoChange();
    });

    const todosSpan = document.createElement('span');
    todosSpan.textContent = 'Todos';

    todosLabel.appendChild(todosCb);
    todosLabel.appendChild(todosSpan);
    container.appendChild(todosLabel);

    // Individual item checkboxes
    items.forEach(item => {
        const label = document.createElement('label');
        label.className = 'flex items-center gap-2 px-1 py-0.5 hover:bg-gray-50 rounded cursor-pointer text-sm';

        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.value = item.value;
        cb.addEventListener('change', () => {
            syncTodosCheckbox(container);
            if (hasCascade) onGenericoChange();
        });

        const span = document.createElement('span');
        span.textContent = item.label;

        label.appendChild(cb);
        label.appendChild(span);
        container.appendChild(label);
    });
}

// Called when a cascading filter changes — reload the target column's values
async function onGenericoChange() {
    const genericoContainer = document.getElementById('filter-generico');
    if (!genericoContainer) return;

    const table = genericoContainer.dataset.table;

    const marcaContainer = document.getElementById('filter-marca');
    if (!marcaContainer) return;

    // Determine selected generico values
    // If "Todos" is checked or nothing is selected, don't pass generico filter (show all marca)
    const allSelected = isAllSelected(genericoContainer);
    const checkedValues = Array.from(
        genericoContainer.querySelectorAll('input[type=checkbox]:checked:not([data-todos])')
    ).map(cb => cb.value);

    marcaContainer.innerHTML = '';
    const loading = document.createElement('span');
    loading.className = 'text-gray-400 text-xs';
    loading.textContent = 'Cargando...';
    marcaContainer.appendChild(loading);

    const qs = new URLSearchParams();
    // Only pass generico filter if there's a partial selection (not all, not none)
    if (!allSelected && checkedValues.length > 0) {
        checkedValues.forEach(v => qs.append('generico', v));
    }
    const url = `/api/filter-values/${encodeURIComponent(table)}` + (qs.toString() ? '?' + qs.toString() : '');
    const res = await authFetch(url);
    if (!res.ok) return;
    const data = await res.json();

    fillCheckboxList(marcaContainer, 'marca', data['marca'] || [], false);
}

// Check if a filter container has "all selected" (Todos checked or every item checked)
function isAllSelected(container) {
    const todosCheckbox = container.querySelector('input[data-todos]');
    if (todosCheckbox && todosCheckbox.checked) return true;
    const itemCheckboxes = container.querySelectorAll('input[type=checkbox]:not([data-todos])');
    if (itemCheckboxes.length === 0) return true;
    return Array.from(itemCheckboxes).every(cb => cb.checked);
}

// Collect active filter selections into [{column, values}], or null if nothing selected.
// Omits a filter entirely when "Todos" / all items are checked (= no restriction).
function collectFilters() {
    if (!currentTable || !(currentTable in TABLE_FILTERS)) return null;

    const filters = [];
    for (const fd of TABLE_FILTERS[currentTable]) {
        const container = document.getElementById(`filter-${fd.col}`);
        if (!container) continue;
        // If all selected, omit this filter (same as "no filter")
        if (isAllSelected(container)) continue;
        const values = Array.from(
            container.querySelectorAll('input[type=checkbox]:checked:not([data-todos])')
        ).map(cb => cb.value);
        if (values.length > 0) {
            filters.push({ column: fd.col, values });
        }
    }
    return filters.length > 0 ? filters : null;
}

function renderColumns() {
    const container = document.getElementById('columnsList');
    container.innerHTML = allColumns.map(col => `
        <label class="column-item flex items-center gap-2 px-2 py-1 rounded cursor-pointer">
            <input type="checkbox" value="${col.name}" onchange="toggleColumn('${col.name}')"
                ${selectedColumns.includes(col.name) ? 'checked' : ''}>
            <span class="text-sm">${col.name}</span>
            <span class="text-xs text-gray-400 ml-auto">${col.type}</span>
        </label>
    `).join('');
    updateSelectedDisplay();
}

function toggleColumn(colName) {
    if (selectedColumns.includes(colName)) {
        selectedColumns = selectedColumns.filter(c => c !== colName);
    } else {
        selectedColumns.push(colName);
    }
    updateSelectedDisplay();
}

function selectAllColumns() {
    selectedColumns = allColumns.map(c => c.name);
    renderColumns();
}

function deselectAllColumns() {
    selectedColumns = [];
    renderColumns();
}

function updateSelectedDisplay() {
    const container = document.getElementById('selectedColumns');
    const countEl = document.getElementById('selectedCount');

    countEl.textContent = `${selectedColumns.length} columnas`;

    if (selectedColumns.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-sm">Ninguna columna seleccionada</p>';
        return;
    }

    container.innerHTML = selectedColumns.map(col => `
        <div class="flex items-center justify-between px-2 py-1 bg-blue-50 rounded text-sm">
            <span>${col}</span>
            <button onclick="toggleColumn('${col}')" class="text-red-500 hover:text-red-700">&times;</button>
        </div>
    `).join('');
}

function updateDateColumnOptions() {
    const dateColumns = allColumns.filter(c =>
        c.type.includes('date') || c.type.includes('timestamp')
    );
    const select = document.getElementById('dateColumn');
    select.innerHTML = '<option value="">Sin filtro</option>' +
        dateColumns.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
}

async function previewData() {
    if (!currentTable || selectedColumns.length === 0) {
        showStatus('Selecciona una tabla y columnas primero', 'error');
        return;
    }

    const filters = collectFilters();
    const body = { table: currentTable, columns: selectedColumns };
    if (filters !== null) body.filters = filters;

    const res = await authFetch('/api/preview', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });
    if (res.status === 401) return;
    const data = await res.json();

    if (data.error) {
        showStatus(data.error, 'error');
        return;
    }

    const section = document.getElementById('previewSection');
    section.classList.remove('hidden');

    document.getElementById('previewCount').textContent = `Mostrando ${data.count} filas`;

    document.getElementById('previewHead').innerHTML = `
        <tr>${data.columns.map(c => `<th class="px-3 py-2 text-left border-b">${c}</th>`).join('')}</tr>
    `;

    document.getElementById('previewBody').innerHTML = data.data.map(row => `
        <tr class="hover:bg-gray-50">${row.map(cell => `<td class="px-3 py-1 border-b text-gray-600">${cell ?? ''}</td>`).join('')}</tr>
    `).join('');
}

async function exportData() {
    if (!currentTable || selectedColumns.length === 0) {
        showStatus('Selecciona una tabla y columnas primero', 'error');
        return;
    }

    const dateColumn = document.getElementById('dateColumn').value;
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;

    showStatus('Exportando...', 'info');

    const filters = collectFilters();
    const body = {
        table: currentTable,
        columns: selectedColumns,
        date_column: dateColumn || null,
        date_from: dateFrom || null,
        date_to: dateTo || null
    };
    if (filters !== null) body.filters = filters;

    const res = await authFetch('/api/export', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });
    if (res.status === 401) return;
    const data = await res.json();

    if (data.error) {
        showStatus(data.error, 'error');
        return;
    }

    // Mostrar aviso de columnas descartadas
    const discardedSection = document.getElementById('discardedSection');
    if (data.discarded_columns && data.discarded_columns.length > 0) {
        discardedSection.classList.remove('hidden');
        document.getElementById('discardedInfo').textContent =
            `${data.discarded_columns.length} descartadas, ${data.exported_columns.length} exportadas`;
        document.getElementById('discardedList').textContent = data.discarded_columns.join(', ');
        showStatus(`Exportado: ${data.filename} (${data.count.toLocaleString()} filas, ${data.discarded_columns.length} columnas descartadas)`, 'success');
    } else {
        discardedSection.classList.add('hidden');
        showStatus(`Exportado: ${data.filename} (${data.count.toLocaleString()} filas)`, 'success');
    }

    // Descargar automaticamente usando un link temporal
    const link = document.createElement('a');
    link.href = `/api/download/${data.filename}`;
    link.download = data.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

async function loadSavedSelections() {
    const res = await authFetch('/api/selections');
    const data = await res.json();
    const select = document.getElementById('savedSelections');
    select.innerHTML = '<option value="">Cargar seleccion...</option>' +
        Object.keys(data.selections).map(name => `<option value="${name}">${name}</option>`).join('');
}

async function loadSelection() {
    const name = document.getElementById('savedSelections').value;
    if (!name) return;

    const res = await authFetch('/api/selections');
    const data = await res.json();
    const selection = data.selections[name];

    if (selection) {
        await selectTable(selection.table);
        selectedColumns = selection.columns;
        renderColumns();
        document.getElementById('selectionName').value = name;
        showStatus(`Seleccion "${name}" cargada`, 'success');
    }
}

async function saveSelection() {
    const name = document.getElementById('selectionName').value.trim();
    if (!name) {
        showStatus('Ingresa un nombre para la seleccion', 'error');
        return;
    }
    if (!currentTable || selectedColumns.length === 0) {
        showStatus('Selecciona una tabla y columnas primero', 'error');
        return;
    }

    const res = await authFetch('/api/selections', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, table: currentTable, columns: selectedColumns})
    });
    if (res.status === 401) return;

    if (res.ok) {
        showStatus(`Seleccion "${name}" guardada`, 'success');
        loadSavedSelections();
    }
}

function showStatus(message, type) {
    const container = document.getElementById('statusMessage');
    const inner = container.querySelector('div');

    container.classList.remove('hidden');
    inner.textContent = message;

    inner.className = 'px-4 py-3 rounded ' + {
        'success': 'bg-green-100 border border-green-400 text-green-700',
        'error': 'bg-red-100 border border-red-400 text-red-700',
        'info': 'bg-blue-100 border border-blue-400 text-blue-700'
    }[type];

    setTimeout(() => container.classList.add('hidden'), 4000);
}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
