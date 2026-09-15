"""Test de fumee : verifie que le module principal s'importe correctement."""
from src.game import settings


def test_settings_loaded() -> None:
    assert settings.SCREEN_WIDTH > 0
    assert settings.SCREEN_HEIGHT > 0
