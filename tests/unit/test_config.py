from backend.config import settings


def test_settings_load_defaults():
    """
    Test that configurations are loaded properly with default values.
    """
    assert settings.APP_ENV in ["development", "testing", "production"]
    assert isinstance(settings.DEBUG, bool)
    assert settings.API_PORT > 0
