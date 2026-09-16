"""Constantes globales du jeu."""

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
