# Pollen Graph Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/graph` page to the Flask app with a Chart.js multi-line chart showing daily pollen concentration by city and date range, driven by an AJAX API endpoint.

**Architecture:** A new `/graph` route renders the page shell; a `/api/graph-data` JSON endpoint handles filtered data queries from SQLite. The frontend fetches data on load and on each Apply click, rebuilds the chart in-place using Chart.js v4, with no page reloads.

**Tech Stack:** Python 3.9, Flask 3.1, SQLite3, Chart.js 4.4.7 (CDN), pytest (test runner), Flask test client (integration tests).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `app/routes.py` | Modify | Add `/graph` and `/api/graph-data` routes; add `jsonify`, `datetime` imports |
| `app/templates/graph.html` | Create | Standalone HTML template: filter bar, canvas, Chart.js script |
| `app/templates/index.html` | Modify | Add `<p><a href="/graph">Graph</a></p>` after `<h1>` |
| `tests/__init__.py` | Create | Makes `tests/` a Python package |
| `tests/conftest.py` | Create | Pytest fixtures: Flask test client with isolated in-memory SQLite DB |
| `tests/test_graph_routes.py` | Create | Integration tests for `/graph` and `/api/graph-data` |
| `requirements.txt` | Modify | Add `pytest` |

---

## Task 1: Set Up Pytest

**Files:**
- Modify: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Add pytest to requirements.txt**

Append to `requirements.txt`:
```
pytest
```

- [ ] **Step 2: Install pytest**

```bash
pip install pytest
```

Expected: installs without errors.

- [ ] **Step 3: Create tests/__init__.py**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 4: Create tests/conftest.py**

```python
import sqlite3
import pytest
from app import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Flask test client with an isolated SQLite DB containing a known schema."""
    db_path = str(tmp_path / "test.db")
    # Patch the local DB_PATH binding inside app.routes (that's what route
    # functions actually reference after `from src.config import DB_PATH`).
    monkeypatch.setattr("app.routes.DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE pollen_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            plant TEXT NOT NULL,
            pollen_concentration TEXT NOT NULL,
            date DATE NOT NULL,
            UNIQUE(city, plant, date)
        )
    """)
    conn.commit()
    conn.close()

    flask_app.config["TESTING"] = True
    return flask_app.test_client()


@pytest.fixture
def client_with_data(client, tmp_path, monkeypatch):
    """Same client but pre-populated with test rows."""
    import app.routes as routes_module
    db_path = routes_module.DB_PATH  # already patched by `client` fixture

    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO pollen_data (city, plant, pollen_concentration, date) VALUES (?, ?, ?, ?)",
        [
            ("Zagreb", "Breza (Betula sp.)", "2.5", "2026-03-01"),
            ("Zagreb", "Breza (Betula sp.)", "3.0", "2026-03-02"),
            ("Zagreb", "Trave (Poaceae)", "1.0", "2026-03-01"),
            ("Zagreb", "Trave (Poaceae)", "bad_value", "2026-03-03"),  # non-numeric — must be excluded
            ("Split", "Maslina (Olea sp.)", "4.0", "2026-03-01"),
        ],
    )
    conn.commit()
    conn.close()
    return client
```

- [ ] **Step 5: Verify pytest discovers the project**

```bash
PYTHONPATH=. pytest tests/ --collect-only
```

Expected: "no tests ran" (0 tests collected — just confirming no import errors).

- [ ] **Step 6: Commit**

```bash
git add requirements.txt tests/__init__.py tests/conftest.py
git commit -m "test: add pytest setup and Flask test client fixture"
```

---

## Task 2: Add `/graph` Route (TDD)

**Files:**
- Modify: `app/routes.py`
- Test: `tests/test_graph_routes.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_graph_routes.py`:

```python
class TestGraphPage:
    def test_returns_200(self, client):
        resp = client.get("/graph")
        assert resp.status_code == 200

    def test_renders_city_select(self, client_with_data):
        resp = client_with_data.get("/graph")
        body = resp.data.decode()
        assert "city-select" in body
        assert "Zagreb" in body
        assert "Split" in body

    def test_cities_sorted_alphabetically(self, client_with_data):
        resp = client_with_data.get("/graph")
        body = resp.data.decode()
        assert body.index("Split") < body.index("Zagreb")

    def test_empty_cities_still_returns_200(self, client):
        resp = client.get("/graph")
        assert resp.status_code == 200
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
PYTHONPATH=. pytest tests/test_graph_routes.py::TestGraphPage -v
```

Expected: 4 errors — `404` or `BuildError` (route doesn't exist yet).

- [ ] **Step 3: Add `/graph` route to app/routes.py**

Add imports at the top of `app/routes.py` (the existing imports are `sqlite3`, `render_template`, `request` from flask, `app` from app, `DB_PATH` from src.config):

```python
from datetime import datetime

from flask import jsonify, render_template, request
```

Then add the route after the existing `index` function:

```python
@app.route('/graph')
def graph():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT city FROM pollen_data ORDER BY city ASC')
    cities = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template('graph.html', cities=cities)
```

Create a minimal `app/templates/graph.html` (just enough to pass the tests — full template comes in Task 4):

```html
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Pollen Graph</title></head>
<body>
<h1>Pollen Graph</h1>
<select id="city-select">
  {% for city in cities %}
  <option value="{{ city }}" {% if loop.first %}selected{% endif %}>{{ city }}</option>
  {% endfor %}
</select>
</body>
</html>
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
PYTHONPATH=. pytest tests/test_graph_routes.py::TestGraphPage -v
```

Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/routes.py app/templates/graph.html tests/test_graph_routes.py
git commit -m "feat: add /graph route with city list"
```

---

## Task 3: Add `/api/graph-data` Route (TDD)

**Files:**
- Modify: `app/routes.py`
- Test: `tests/test_graph_routes.py` (add new class)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_graph_routes.py`:

```python
class TestGraphDataApi:
    def test_missing_city_returns_400(self, client):
        resp = client.get("/api/graph-data")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "city is required"

    def test_empty_city_returns_400(self, client):
        resp = client.get("/api/graph-data?city=")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "city is required"

    def test_bad_date_from_format_returns_400(self, client):
        resp = client.get("/api/graph-data?city=Zagreb&date_from=not-a-date")
        assert resp.status_code == 400
        assert "invalid date format" in resp.get_json()["error"]

    def test_bad_date_to_format_returns_400(self, client):
        resp = client.get("/api/graph-data?city=Zagreb&date_to=31-03-2026")
        assert resp.status_code == 400
        assert "invalid date format" in resp.get_json()["error"]

    def test_date_from_after_date_to_returns_400(self, client):
        resp = client.get("/api/graph-data?city=Zagreb&date_from=2026-03-31&date_to=2026-03-01")
        assert resp.status_code == 400
        assert "date_from must not be after date_to" in resp.get_json()["error"]

    def test_returns_empty_list_when_no_data(self, client):
        resp = client.get("/api/graph-data?city=Zagreb&date_from=2026-03-01&date_to=2026-03-31")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_data_for_city_and_range(self, client_with_data):
        resp = client_with_data.get(
            "/api/graph-data?city=Zagreb&date_from=2026-03-01&date_to=2026-03-31"
        )
        assert resp.status_code == 200
        rows = resp.get_json()
        assert len(rows) == 3  # 2 Breza + 1 Trave (bad_value row excluded)
        plants = {r["plant"] for r in rows}
        assert "Breza (Betula sp.)" in plants
        assert "Trave (Poaceae)" in plants

    def test_excludes_non_numeric_concentration(self, client_with_data):
        resp = client_with_data.get(
            "/api/graph-data?city=Zagreb&date_from=2026-03-01&date_to=2026-03-31"
        )
        rows = resp.get_json()
        # "bad_value" row for Trave on 2026-03-03 must not appear
        trave_rows = [r for r in rows if r["plant"] == "Trave (Poaceae)"]
        assert len(trave_rows) == 1
        assert trave_rows[0]["date"] == "2026-03-01"

    def test_response_shape(self, client_with_data):
        resp = client_with_data.get(
            "/api/graph-data?city=Zagreb&date_from=2026-03-01&date_to=2026-03-02"
        )
        rows = resp.get_json()
        assert len(rows) > 0
        row = rows[0]
        assert set(row.keys()) == {"plant", "date", "concentration"}
        assert isinstance(row["concentration"], float)

    def test_filters_by_city(self, client_with_data):
        resp = client_with_data.get(
            "/api/graph-data?city=Split&date_from=2026-03-01&date_to=2026-03-31"
        )
        rows = resp.get_json()
        assert all(r["plant"] == "Maslina (Olea sp.)" for r in rows)

    def test_ordered_by_date_asc(self, client_with_data):
        resp = client_with_data.get(
            "/api/graph-data?city=Zagreb&date_from=2026-03-01&date_to=2026-03-31"
        )
        rows = resp.get_json()
        dates = [r["date"] for r in rows]
        assert dates == sorted(dates)

    def test_date_defaults_do_not_crash(self, client_with_data):
        """When date params are omitted, server fills defaults and returns 200."""
        resp = client_with_data.get("/api/graph-data?city=Zagreb")
        assert resp.status_code == 200
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
PYTHONPATH=. pytest tests/test_graph_routes.py::TestGraphDataApi -v
```

Expected: all fail with 404 (route not yet defined).

- [ ] **Step 3: Implement `/api/graph-data` in app/routes.py**

Add after the `graph()` function:

```python
@app.route('/api/graph-data')
def graph_data():
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400

    today = datetime.today()
    first_of_month = today.replace(day=1)

    date_from_str = request.args.get('date_from', '').strip() or first_of_month.strftime('%Y-%m-%d')
    date_to_str = request.args.get('date_to', '').strip() or today.strftime('%Y-%m-%d')

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'invalid date format, expected YYYY-MM-DD'}), 400

    if date_from > date_to:
        return jsonify({'error': 'date_from must not be after date_to'}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT plant, date, pollen_concentration FROM pollen_data '
        'WHERE city = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
        (city, date_from_str, date_to_str)
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for plant, date, concentration in rows:
        try:
            result.append({
                'plant': plant,
                'date': date,
                'concentration': float(concentration)
            })
        except ValueError:
            pass  # skip non-numeric rows

    return jsonify(result)
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
PYTHONPATH=. pytest tests/test_graph_routes.py -v
```

Expected: all tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/routes.py tests/test_graph_routes.py
git commit -m "feat: add /api/graph-data endpoint with validation and filtering"
```

---

## Task 4: Build graph.html Template

**Files:**
- Modify: `app/templates/graph.html` (replace the minimal stub from Task 2)

- [ ] **Step 1: Replace graph.html with the full template**

Overwrite `app/templates/graph.html` with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Pollen Graph</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
</head>
<body>
  <h1>Pollen Concentration Graph</h1>
  <p><a href="/">Table view</a></p>

  <form id="filter-form">
    <label for="city-select">City:</label>
    <select id="city-select">
      {% for city in cities %}
      <option value="{{ city }}" {% if loop.first %}selected{% endif %}>{{ city }}</option>
      {% endfor %}
    </select>

    <label for="date-from">From:</label>
    <input type="date" id="date-from">

    <label for="date-to">To:</label>
    <input type="date" id="date-to">

    <button type="button" id="apply-btn">Apply</button>
  </form>

  <p id="error-msg" style="display:none;color:red"></p>
  <p id="no-data-msg" style="display:none">No data for this selection.</p>
  <canvas id="pollen-chart" style="display:none"></canvas>

  <script>
    const PALETTE = [
      '#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
      '#0891b2','#be185d','#92400e','#065f46','#1e3a5f'
    ];

    let chart = null;

    function formatDate(d) {
      return d.toISOString().slice(0, 10);
    }

    async function fetchAndRender() {
      const errorMsg = document.getElementById('error-msg');
      const noDataMsg = document.getElementById('no-data-msg');
      const canvas = document.getElementById('pollen-chart');

      try {
        const city = document.getElementById('city-select').value;
        if (!city) {
          errorMsg.textContent = 'No cities available';
          errorMsg.style.display = '';
          return;
        }

        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;

        if (dateFrom > dateTo) {
          errorMsg.textContent = 'Start date must not be after end date';
          errorMsg.style.display = '';
          return;
        }

        errorMsg.style.display = 'none';

        const url = `/api/graph-data?city=${encodeURIComponent(city)}&date_from=${dateFrom}&date_to=${dateTo}`;
        const resp = await fetch(url);

        if (!resp.ok) {
          let msg = 'Request failed';
          try { msg = (await resp.json()).error || msg; } catch (_) {}
          errorMsg.textContent = msg;
          errorMsg.style.display = '';
          canvas.style.display = 'none';
          noDataMsg.style.display = 'none';
          return;
        }

        const rows = await resp.json();

        if (rows.length === 0) {
          if (chart) { chart.destroy(); chart = null; }
          canvas.style.display = 'none';
          noDataMsg.style.display = '';
          return;
        }

        noDataMsg.style.display = 'none';
        errorMsg.style.display = 'none';
        canvas.style.display = '';

        // Group by plant
        const byPlant = {};
        for (const row of rows) {
          if (!byPlant[row.plant]) byPlant[row.plant] = {};
          byPlant[row.plant][row.date] = row.concentration;
        }

        // Build shared labels (all unique dates, sorted)
        const labels = [...new Set(rows.map(r => r.date))].sort();

        const datasets = Object.entries(byPlant).map(([plant, dateMap], i) => {
          const color = PALETTE[i % PALETTE.length];
          return {
            label: plant,
            data: labels.map(d => dateMap[d] ?? null),
            borderColor: color,
            backgroundColor: color + '22',
            tension: 0.3,
            spanGaps: true,
            pointRadius: 3
          };
        });

        if (chart) chart.destroy();
        chart = new Chart(canvas, {
          type: 'line',
          data: { labels, datasets },
          options: {
            responsive: true,
            plugins: {
              legend: { position: 'bottom', labels: { boxWidth: 12, padding: 16 } },
              tooltip: { mode: 'index', intersect: false }
            },
            scales: {
              y: { beginAtZero: true, title: { display: true, text: 'Concentration' } },
              x: { title: { display: true, text: 'Date' } }
            }
          }
        });

      } catch (err) {
        const errorMsg = document.getElementById('error-msg');
        errorMsg.textContent = 'Network error';
        errorMsg.style.display = '';
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      const today = new Date();
      const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      document.getElementById('date-from').value = formatDate(firstOfMonth);
      document.getElementById('date-to').value = formatDate(today);

      document.getElementById('apply-btn').addEventListener('click', () => { fetchAndRender(); });

      fetchAndRender();
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Run existing tests to confirm nothing is broken**

```bash
PYTHONPATH=. pytest tests/test_graph_routes.py -v
```

Expected: all tests still PASSED (the test for `city-select` still passes because the element is still in the template).

- [ ] **Step 3: Commit**

```bash
git add app/templates/graph.html
git commit -m "feat: add graph.html template with Chart.js and AJAX filter"
```

---

## Task 5: Add Navigation Link to index.html

**Files:**
- Modify: `app/templates/index.html`

- [ ] **Step 1: Add link after the `<h1>` in index.html**

In `app/templates/index.html`, the current `<h1>` line is:
```html
    <h1>Pollen Data per Month and City</h1>
```

Add immediately after it:
```html
    <p><a href="/graph">Graph</a></p>
```

- [ ] **Step 2: Verify the index page still loads**

```bash
PYTHONPATH=. pytest tests/ -v
```

Expected: all tests PASSED (no regressions).

- [ ] **Step 3: Commit**

```bash
git add app/templates/index.html
git commit -m "feat: add Graph nav link to index page"
```

---

## Manual Smoke Test (Final Verification)

- [ ] **Start the Flask app**

```bash
PYTHONPATH=. python run.py
```

- [ ] **Open http://localhost:5000 — verify "Graph" link is present**

- [ ] **Open http://localhost:5000/graph — verify:**
  - City dropdown is populated
  - Date inputs default to current month
  - Chart renders on load (or "No data" message if DB is empty for current month)
  - Changing city/dates and clicking Apply updates the chart without page reload
  - Selecting a range with no data shows "No data for this selection."
