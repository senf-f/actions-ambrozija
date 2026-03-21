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
