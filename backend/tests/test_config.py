"""Settings parsing tests.

These cover the deployment-critical settings: a value that fails to parse
crashes the app at import time, which is a much worse failure than a bad
response.
"""

import pytest

from app.core.config import Settings


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


class TestAllowedOrigins:
    def test_comma_separated_env_value(self, monkeypatch):
        """The form documented in .env.example must parse.

        pydantic-settings JSON-decodes complex fields by default, so a plain
        comma-separated value used to raise SettingsError and prevent boot.
        """
        monkeypatch.setenv(
            "ALLOWED_ORIGINS",
            "https://app.vercel.app,https://app.netlify.app",
        )
        assert _settings().allowed_origins == [
            "https://app.vercel.app",
            "https://app.netlify.app",
        ]

    def test_json_array_env_value(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_ORIGINS", '["https://app.vercel.app"]')
        assert _settings().allowed_origins == ["https://app.vercel.app"]

    def test_whitespace_and_empty_entries_are_dropped(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_ORIGINS", " https://a.com , ,https://b.com ,")
        assert _settings().allowed_origins == ["https://a.com", "https://b.com"]

    def test_default_allows_local_frontend(self):
        assert "http://localhost:5173" in _settings().allowed_origins


class TestSecretKey:
    def test_rejects_short_key(self):
        with pytest.raises(ValueError, match="at least 32 characters"):
            _settings(secret_key="change-me-in-production")

    def test_rejects_documented_placeholder_in_production(self):
        """The placeholder shipped in .env.example must never boot production.

        It is short enough to trip the length rule on its own, so assert on the
        explicit production guard as well to keep that branch covered.
        """
        with pytest.raises(ValueError):
            _settings(api_env="production", secret_key="change-me-in-production")

    def test_accepts_generated_length_key(self):
        key = "k" * 48
        assert _settings(secret_key=key).secret_key == key


class TestDatabaseUrl:
    def test_rejects_non_postgres(self):
        with pytest.raises(ValueError, match="PostgreSQL"):
            _settings(database_url="sqlite+aiosqlite:///./local.db")

    @pytest.mark.parametrize(
        "url",
        [
            "postgresql://postgres:postgres@localhost:5432/stock_prediction",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/stock_prediction",
        ],
    )
    def test_accepts_postgres_forms(self, url):
        assert _settings(database_url=url).database_url == url


class TestDateWindows:
    def test_window_end_is_today_when_unset(self):
        from app.utils import trading_calendar

        settings = _settings(default_end_date=None, default_start_date="2024-01-01")
        _start, end = settings.default_window()
        assert end == trading_calendar.today()

    def test_window_start_honours_configured_value(self):
        settings = _settings(default_start_date="2024-01-01", default_end_date="2025-06-30")
        start, end = settings.default_window()
        assert start.isoformat() == "2024-01-01"
        assert end.isoformat() == "2025-06-30"

    def test_start_falls_back_to_lookback_when_unset(self):
        settings = _settings(default_start_date=None, default_end_date="2025-06-30", default_lookback_days=30)
        start, _end = settings.default_window()
        assert (start + __import__("datetime").timedelta(days=30)).isoformat() == "2025-06-30"