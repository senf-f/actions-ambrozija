class TestComparePage:
    def test_returns_200(self, client):
        resp = client.get("/compare")
        assert resp.status_code == 200

    def test_renders_city_select(self, client_with_data):
        resp = client_with_data.get("/compare")
        body = resp.data.decode()
        assert "city-select" in body
        assert "Zagreb" in body
        assert "Split" in body

    def test_cities_sorted_alphabetically(self, client_with_data):
        resp = client_with_data.get("/compare")
        body = resp.data.decode()
        assert body.index("Split") < body.index("Zagreb")

    def test_empty_cities_still_returns_200(self, client):
        resp = client.get("/compare")
        assert resp.status_code == 200

    def test_renders_plant_select(self, client):
        resp = client.get("/compare")
        body = resp.data.decode()
        assert "plant-select" in body

    def test_renders_period_controls(self, client):
        resp = client.get("/compare")
        body = resp.data.decode()
        assert "periods" in body
        assert "add-period" in body


class TestPlantsApi:
    def test_missing_city_returns_400(self, client):
        resp = client.get("/api/plants")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "city is required"

    def test_empty_city_returns_400(self, client):
        resp = client.get("/api/plants?city=")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "city is required"

    def test_returns_distinct_plants_for_city(self, client_with_data):
        resp = client_with_data.get("/api/plants?city=Zagreb")
        assert resp.status_code == 200
        plants = resp.get_json()
        assert set(plants) == {"Breza (Betula sp.)", "Trave (Poaceae)"}

    def test_filters_by_city(self, client_with_data):
        resp = client_with_data.get("/api/plants?city=Split")
        assert resp.status_code == 200
        assert resp.get_json() == ["Maslina (Olea sp.)"]

    def test_plants_sorted_alphabetically(self, client_with_data):
        resp = client_with_data.get("/api/plants?city=Zagreb")
        plants = resp.get_json()
        assert plants == sorted(plants)

    def test_unknown_city_returns_empty_list(self, client_with_data):
        resp = client_with_data.get("/api/plants?city=Nonexistent")
        assert resp.status_code == 200
        assert resp.get_json() == []
