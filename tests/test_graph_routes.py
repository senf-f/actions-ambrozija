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

    def test_renders_period_pills(self, client):
        resp = client.get("/graph")
        body = resp.data.decode()
        assert "pill-current" in body
        assert "pill-prev" in body
        assert "Ovaj mjesec" in body
        assert "Prošli mjesec" in body

    def test_pills_coexist_with_date_inputs(self, client):
        resp = client.get("/graph")
        body = resp.data.decode()
        assert "date-from" in body
        assert "date-to" in body
        assert "pill-group" in body


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
        assert len(rows) == 1
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
        assert isinstance(resp.get_json(), list)
