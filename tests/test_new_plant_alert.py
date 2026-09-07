from src import telegram
from src.main import unknown_plants


def test_known_plants_raise_no_alert():
    assert unknown_plants(["Ambrozija (Ambrosia sp.)", "Trave (Poaceae)"]) == []


def test_unlisted_plant_is_reported():
    assert unknown_plants(["Trave (Poaceae)", "Maslačak (Taraxacum sp.)"]) == [
        "Maslačak (Taraxacum sp.)"
    ]


def test_send_is_a_noop_without_credentials(monkeypatch, capsys):
    monkeypatch.delenv("TELEGRAM_API_TOKEN_STAMPAR", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    def fail(*args, **kwargs):
        raise AssertionError("must not call the API without credentials")

    monkeypatch.setattr(telegram.requests, "post", fail)

    telegram.send("Nove biljke: x")
    assert "not configured" in capsys.readouterr().out
