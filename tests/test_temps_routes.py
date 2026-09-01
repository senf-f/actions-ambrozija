from src.config import AIR_STATIONS, SEA_STATIONS


class TestTempsPage:
    def test_returns_200(self, client):
        resp = client.get("/temps")
        assert resp.status_code == 200

    def test_defaults_to_split(self, client):
        body = client.get("/temps").data.decode()
        assert '<option value="Split" selected>' in body

    def test_lists_every_air_and_sea_city(self, client):
        """Cities come from config, so they are listed even with an empty DB."""
        body = client.get("/temps").data.decode()
        for city in set(AIR_STATIONS.values()) | set(SEA_STATIONS):
            assert f'value="{city}"' in body

    def test_renders_date_range_inputs(self, client):
        body = client.get("/temps").data.decode()
        assert 'id="date-from"' in body
        assert 'id="date-to"' in body
