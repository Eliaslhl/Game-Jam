from pathlib import Path

"""Constantes globales du jeu."""

PROJECT_ROOT = Path(__file__).resolve().parent
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
SOUNDS_DIR = PROJECT_ROOT / "assets" / "sounds"
IMAGES_DIR = PROJECT_ROOT / "assets" / "images"
BACKGROUND_MUSIC = SOUNDS_DIR / "music_fond.wav"
BACKGROUND_MUSIC_VOLUME = 0.35

# Logo rond du jeu, affiche a la place du titre dans le menu principal.
LOGO_FILE = IMAGES_DIR / "logo.jpeg"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Witch or Ghost"

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


TITLE_FONT_FILE = FONTS_DIR / "MedievalSharp-Regular.ttf"
UI_FONT_FILE = FONTS_DIR / "MedievalSharp-Regular.ttf"


"""Colors (ancienne DA menu - a remplacer)"""

BACKGROUND = (30, 24, 18)
PARCHMENT = (222, 198, 156)
TITLE = (196, 30, 30)
WOOD = (92, 64, 42)
WOOD_LIGHT = (120, 84, 56)
DIM = (120, 114, 104)


"""Colors (DA pixel-art de Kadir, cf. views/training_map_view.py)"""

INK = (12, 17, 25)
GOLD = (224, 191, 119)
PALE = (222, 225, 216)

TEXT_DIM = (136, 149, 157)
DIVIDER = (61, 65, 64)

GHOST_STATUS = (154, 222, 211)
GHOST_BAR_BG = (43, 48, 63)
GHOST_BAR_FILL = (172, 136, 223)
POTION_COUNT = (192, 150, 228)
CORPSE = (118, 105, 109)

KEY_TILE_BG = (64, 62, 63)
KEY_TILE_BORDER = (129, 108, 58)
KEY_TILE_TEETH = (245, 209, 110)
KEY_TILE_GHOST_GLOW = (155, 239, 226)

EXIT_TILE_BG = (29, 55, 49)
EXIT_TILE_BORDER = (119, 232, 155)

TORCH_WOOD = (93, 60, 39)
TORCH_FLAME = (205, 112, 47)
TORCH_FLAME_CORE = (255, 223, 131)

GHOST_SPRITE_LIGHT = (235, 238, 240)
GHOST_SPRITE_DARK = (196, 202, 208)

WIN_VEIL = (6, 16, 22, 220)
PLAYER_SHADOW = (12, 19, 27)
