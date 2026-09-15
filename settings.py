from pathlib import Path
import arcade

"""Constantes globales du jeu."""

PROJECT_ROOT = Path(__file__).resolve().parent
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

print(FONTS_DIR)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Deadweight"

TILE_SIZE = 64

PLAYER_SPEED = 4
PLAYER_MAX_HP = 100

# Types de tuiles du prototype de labyrinthe de Thais (systems/level_manager.py,
# views/game_view.py) : un caractere = une case, dans le plan texte du niveau.
VIDE = "."
MUR = "#"              # infranchissable, vivant ou fantome
MUR_FISSURE = "~"      # franchissable uniquement en fantome
PORTE = "P"            # franchissable uniquement vivant (et si deverrouillee)
CLE = "C"              # ramassable uniquement vivant
LEVIER = "L"           # activable uniquement vivant
FIOLE = "F"
SORTIE = "S"           # fin du niveau, necessite une clef

# Difficulte = temps limite pour sortir du labyrinthe (en secondes)
TEMPS_LIMITE_NIVEAU_1 = 90

GHOST_MODE_DURATION = 10.0
GHOST_MODE_SPEED = 5
FIOLES_DEPART = 3
POISON_VIAL_START_COUNT = 3
RESURRECTION_VIAL_START_COUNT = 3
LIFE_VIAL_START_COUNT = RESURRECTION_VIAL_START_COUNT


"""Fonts"""

FONT_TITLE = ("MedievalSharp", "Georgia", "serif")
FONT_UI = ("MedievalSharp", "Georgia", "serif")

_FONT_FILES = [
    "MedievalSharp-Regular.ttf",
]

def load_fonts() -> None:
    for filename in _FONT_FILES:
        path = FONTS_DIR / filename
        if path.exists():
            arcade.load_font(path)
        else:
            print("Font not found")

"""Colors"""

BACKGROUND = (30, 24, 18)
PARCHMENT = (222, 198, 156)
TITLE = (196, 30, 30)
WOOD = (92, 64, 42)
WOOD_LIGHT = (120, 84, 56)
DIM = (120, 114, 104)
