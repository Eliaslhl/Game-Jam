"""Chargement des niveaux depuis les fichiers de `levels/data/` (Tiled ou JSON).

Responsable : Melissa
"""
from pathlib import Path

LEVELS_DATA_DIR = Path(__file__).parent / "data"


def load_level(level_name: str):
    """Charge et retourne la scene/maze correspondant a `level_name`."""
