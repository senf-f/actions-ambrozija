import pytest
import requests

from src import dhmz


class FakeResponse:
    def __init__(self, body):
        self.content = body

    def raise_for_status(self):
        pass


def test_falls_back_to_http_when_certificate_fails(monkeypatch):
    tried = []

    def fake_get(url, timeout=None):
        tried.append(url)
        if url.startswith('https://'):
            raise requests.exceptions.SSLError('hostname mismatch')
        return FakeResponse(b'<x/>')

    monkeypatch.setattr(dhmz.requests, 'get', fake_get)

    assert dhmz.fetch_xml('https://vrijeme.hr/tx.xml') == b'<x/>'
    assert tried == ['https://vrijeme.hr/tx.xml', 'http://vrijeme.hr/tx.xml']


def test_https_is_not_downgraded_when_it_works(monkeypatch):
    tried = []

    def fake_get(url, timeout=None):
        tried.append(url)
        return FakeResponse(b'<x/>')

    monkeypatch.setattr(dhmz.requests, 'get', fake_get)

    dhmz.fetch_xml('https://vrijeme.hr/tx.xml')
    assert tried == ['https://vrijeme.hr/tx.xml']


def test_other_network_errors_still_raise(monkeypatch):
    def boom(url, timeout=None):
        raise requests.ConnectionError('down')

    monkeypatch.setattr(dhmz.requests, 'get', boom)

    with pytest.raises(requests.ConnectionError):
        dhmz.fetch_xml('https://vrijeme.hr/tx.xml')
