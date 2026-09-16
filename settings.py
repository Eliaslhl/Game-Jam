# Responsable : à assigner — constantes partagées par tout le jeu

TILE_SIZE = 64
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Deadweight"  # à remplacer par le nom retenu par l'équipe

# Types de tuiles du labyrinthe (un caractère = une case, dans les plans de niveau)
VIDE = "."
MUR = "#"              # infranchissable, vivant ou fantôme
MUR_FISSURE = "~"      # franchissable uniquement en fantôme
PORTE = "P"            # franchissable uniquement vivant (et si déverrouillée)
CLE = "C"              # ramassable uniquement vivant
LEVIER = "L"           # activable uniquement vivant
FIOLE = "F"
SORTIE = "S"           # fin du niveau, nécessite une clé

# Chaque fiole de poison a une fiole de vie correspondante.
FIOLES_DEPART = 3
POISON_VIAL_START_COUNT = FIOLES_DEPART
LIFE_VIAL_START_COUNT = POISON_VIAL_START_COUNT

# Difficulté = temps limite pour sortir du labyrinthe (en secondes)
TEMPS_LIMITE_NIVEAU_1 = 90
GHOST_MODE_DURATION = 10.0
