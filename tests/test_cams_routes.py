import pytest
import requests

import app.routes as routes


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


HOURLY = {
    'hourly': {
        'time': [
            '2026-09-01T00:00', '2026-09-01T12:00', '2026-09-01T18:00',
            '2026-09-02T00:00', '2026-09-02T13:00',
        ],
        'ragweed_pollen': [10.0, 182.5, 40.0, None, 55.5],
    }
}


@pytest.fixture
def captured(monkeypatch):
    """Stub the upstream call and record the params it was given."""
    calls = {}

    def fake_get(url, timeout=None, params=None):
        calls['url'] = url
        calls['params'] = params
        return FakeResponse(HOURLY)

    monkeypatch.setattr(routes.requests, 'get', fake_get)
    return calls


class TestCamsData:
    def test_reduces_hourly_to_daily_max(self, client, captured):
        resp = client.get('/api/cams-data?city=Zagreb&date_from=2026-09-01&date_to=2026-09-02')
        assert resp.status_code == 200
        # None readings are skipped, not treated as zero
        assert resp.get_json() == [
            {'date': '2026-09-01', 'grains': 182.5},
            {'date': '2026-09-02', 'grains': 55.5},
        ]

    def test_requests_the_city_coordinates(self, client, captured):
        client.get('/api/cams-data?city=Split&date_from=2026-09-01&date_to=2026-09-02')
        assert (captured['params']['latitude'], captured['params']['longitude']) == (43.5081, 16.4402)
        assert captured['params']['hourly'] == 'ragweed_pollen'

    def test_unknown_city_returns_empty_without_calling_upstream(self, client, captured):
        resp = client.get('/api/cams-data?city=Nigdjezemska&date_from=2026-09-01&date_to=2026-09-02')
        assert resp.status_code == 200
        assert resp.get_json() == []
        assert 'params' not in captured

    def test_range_older_than_upstream_window_is_not_requested(self, client, captured):
        """Upstream only keeps ~92 days, so an old range must not be fetched."""
        resp = client.get('/api/cams-data?city=Zagreb&date_from=2020-08-01&date_to=2020-08-31')
        assert resp.get_json() == []
        assert 'params' not in captured

    def test_city_is_required(self, client, captured):
        assert client.get('/api/cams-data').status_code == 400

    def test_upstream_failure_reports_502(self, client, monkeypatch):
        def boom(url, timeout=None, params=None):
            raise requests.ConnectionError('down')

        monkeypatch.setattr(routes.requests, 'get', boom)
        assert client.get('/api/cams-data?city=Zagreb').status_code == 502
