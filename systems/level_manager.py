# Responsable : à assigner — construction du labyrinthe à partir d'un plan texte

import arcade
from settings import TILE_SIZE, MUR, MUR_FISSURE, PORTE, CLE, FIOLE, LEVIER, SORTIE


def charger_labyrinthe(plan):
    """
    plan : liste de chaînes de caractères, une case = un caractère (voir constants.py).
    Retourne :
      - maze_grid : dict {(x, y): caractère} pour tester les déplacements
      - sprites_murs : SpriteList des murs à dessiner
      - objets : liste de (x, y, caractère) pour clés/fioles/leviers/porte/sortie
    """
    maze_grid = {}
    sprites_murs = arcade.SpriteList()
    objets = []

    hauteur = len(plan)
    for row_index, ligne in enumerate(plan):
        y = hauteur - 1 - row_index  # inverse la lecture : (0,0) en bas à gauche comme Arcade
        for x, caractere in enumerate(ligne):
            maze_grid[(x, y)] = caractere
            px = x * TILE_SIZE + TILE_SIZE // 2
            py = y * TILE_SIZE + TILE_SIZE // 2

            if caractere == MUR:
                mur = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.DARK_GRAY)
                mur.center_x, mur.center_y = px, py
                sprites_murs.append(mur)
            elif caractere == MUR_FISSURE:
                mur = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.GOLD)
                mur.center_x, mur.center_y = px, py
                sprites_murs.append(mur)
            elif caractere in (PORTE, CLE, FIOLE, LEVIER, SORTIE):
                objets.append((x, y, caractere))

    return maze_grid, sprites_murs, objets


# Plan d'exemple — à remplacer par vos propres labyrinthes.
# S = sortie, P = porte, C = clé, F = fiole, L = levier, ~ = mur fissuré
PLAN_NIVEAU_1 = [
    "###########",
    "#....#....#",
    "#.##.#.##.#",
    "#.#..C..#.#",
    "#.#.###.#.#",
    "#...~F~...#",
    "###.#.#####",
    "#.......L.#",
    "#.#######.#",
    "#.........#",
    "#####P#####",
    "#####S#####",
]
