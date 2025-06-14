import os
from ai_backend.app.config import get_settings


def test_get_settings_uses_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "testkey")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "servicekey")
    settings = get_settings()
    assert settings.gemini_api_key == "testkey"
    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.supabase_key == "servicekey"
