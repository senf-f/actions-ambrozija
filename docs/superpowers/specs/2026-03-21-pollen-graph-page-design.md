# Pollen Graph Page — Design Spec

**Date:** 2026-03-21
**Status:** Approved

## Overview

Add a `/graph` page to the existing Flask web app that displays daily pollen concentration data as a multi-line chart, with filtering by city and date range.

## Goals

- Visualise pollen concentration over time for a selected city and date range
- Show all plant species as separate coloured lines on one chart
- Default view: current month, first city alphabetically
- No page reloads when applying filters (dynamic AJAX)

## Architecture

### New Routes (app/routes.py)

**Imports to add:** `jsonify` from `flask` (in addition to the existing `render_template`, `request`); `from datetime import datetime` from the standard library.

**`GET /graph`**
- Queries `SELECT DISTINCT city FROM pollen_data ORDER BY city ASC`
- Renders `graph.html` with `cities` list
- If `cities` is empty, renders the page with an empty dropdown and no chart

**`GET /api/graph-data`**
- Query params:
  - `city` — read with `request.args.get('city', '').strip()`; if falsy (`not city`), return `jsonify({"error": "city is required"}), 400`
  - `date_from` (optional, YYYY-MM-DD) — if absent or empty, default to first day of current month
  - `date_to` (optional, YYYY-MM-DD) — if absent or empty, default to today
  - Server-side defaults exist for direct API callers; the browser always sends both params explicitly
- Date validation — applied to the final values **after** defaults are filled in:
  - Parse both with `datetime.strptime(value, "%Y-%m-%d")`; if either raises `ValueError`, return `jsonify({"error": "invalid date format, expected YYYY-MM-DD"}), 400`
  - If parsed `date_from > date_to`, return `jsonify({"error": "date_from must not be after date_to"}), 400`
- SQL: `SELECT plant, date, pollen_concentration FROM pollen_data WHERE city = ? AND date BETWEEN ? AND ? ORDER BY date ASC`
- Non-numeric rows excluded with Python post-filter: skip rows where `float(pollen_concentration)` raises `ValueError`
- Returns `jsonify([{ "plant": "...", "date": "YYYY-MM-DD", "concentration": 1.5 }, ...])`
- DB connection: `conn = sqlite3.connect(DB_PATH)`, `cursor = conn.cursor()`, `cursor.execute(...)`, `rows = cursor.fetchall()`, `conn.close()` — same pattern as the existing `index` route

### Frontend (app/templates/graph.html)

**Template structure:** standalone HTML document (same pattern as `index.html`); includes `<link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">`.

**Chart.js:** `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>`

**Filter bar:**
- City `<select id="city-select">` populated via Jinja; the first `<option>` has the `selected` attribute
- `<input type="date" id="date-from">` — JS sets `value` on `DOMContentLoaded`
- `<input type="date" id="date-to">` — JS sets `value` on `DOMContentLoaded`
- `<button id="apply-btn">Apply</button>`
- `<p id="error-msg" style="display:none;color:red"></p>`

**Chart area:**
- `<p id="no-data-msg" style="display:none">No data for this selection.</p>`
- `<canvas id="pollen-chart" style="display:none"></canvas>`

**JS — module-level variable:** `let chart = null;` at the top of the `<script>` block.

**Colour palette** (cycle by `i % palette.length`):
```
['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed','#0891b2','#be185d','#92400e','#065f46','#1e3a5f']
```

**`fetchAndRender()` function** — declared as `async function fetchAndRender()`. Wrap the entire body in a `try/catch`; on a caught error (e.g. network offline), show `#error-msg` with "Network error" and return.

1. Read city from `#city-select`. If empty string (no options in dropdown), show `#error-msg` with "No cities available" and return without fetching.
2. Read `date_from` and `date_to` from inputs.
3. Client-side: if `date_from > date_to` (YYYY-MM-DD string compare), show `#error-msg` with "Start date must not be after end date" and return.
4. Hide `#error-msg`.
5. `const resp = await fetch('/api/graph-data?city=...&date_from=...&date_to=...')`
6. If `!resp.ok`: parse body as JSON with `try/catch`; show `#error-msg` with `parsed.error` if available, otherwise "Request failed"; hide `#pollen-chart`; hide `#no-data-msg`; return.
7. `const rows = await resp.json()`
8. If `rows.length === 0`: if `chart` exists call `chart.destroy()` and set `chart = null`; hide `#pollen-chart`; show `#no-data-msg`; return.
9. Hide `#no-data-msg`; hide `#error-msg`; show `#pollen-chart`.
10. Group rows by plant. Build shared `labels` array = all unique date strings across all plants, sorted ascending.
11. For each plant, build `data` array aligned to `labels`: for each label date, find the matching row's `concentration`, or `null` if absent.
12. If `chart` exists call `chart.destroy()`.
13. Create new `Chart(document.getElementById('pollen-chart'), { ... })` and assign to `chart`.

**Data flow on load:**
- On `DOMContentLoaded`: set `#date-from` to first day of current month (YYYY-MM-DD), `#date-to` to today (YYYY-MM-DD); call `fetchAndRender()`.
- `#apply-btn` click handler: `document.getElementById('apply-btn').addEventListener('click', () => { fetchAndRender(); })` — fire-and-forget (no `await` needed in the handler).

**Chart.js config:**
- `type: 'line'`
- `data: { labels, datasets }` where each dataset is `{ label: plantName, data: concentrationArray, borderColor: color, backgroundColor: color + '22', tension: 0.3, spanGaps: true, pointRadius: 3 }`
- `options.plugins.legend`: `{ position: 'bottom', labels: { boxWidth: 12, padding: 16 } }`
- `options.plugins.tooltip`: `{ mode: 'index', intersect: false }`
- `options.scales.y`: `{ beginAtZero: true, title: { display: true, text: 'Concentration' } }`
- `options.scales.x`: `{ title: { display: true, text: 'Date' } }`

### Navigation

In `app/templates/index.html`, add `<p><a href="/graph">Graph</a></p>` immediately after the `<h1>` element.

## Files Changed

| File | Change |
|---|---|
| `app/routes.py` | Add `jsonify`, `datetime` imports; add `/graph` and `/api/graph-data` routes |
| `app/templates/graph.html` | New standalone template |
| `app/templates/index.html` | Add `<p><a href="/graph">Graph</a></p>` after `<h1>` |

## Dependencies

No new Python packages. Chart.js 4.4.7 from jsDelivr CDN.

## Out of Scope

- Plant filter (all plants shown for the selected city/range)
- Multiple cities on the same chart
- Export / download
