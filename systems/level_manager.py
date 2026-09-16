# Responsable : Thaïs — construction du labyrinthe à partir d'un plan texte

import pygame

from settings import TILE_SIZE, MUR, MUR_FISSURE, PORTE, CLE, FIOLE, LEVIER, SORTIE


def charger_labyrinthe(plan):
    """
    plan : liste de chaînes de caractères, une case = un caractère (voir constants.py).
    Retourne :
    - murs : liste de pygame.Rect à dessiner
      - objets : liste de (x, y, caractère) pour clés/fioles/leviers/porte/sortie
    """
    maze_grid = {}
    murs = []
    objets = []

    hauteur = len(plan)
    for row_index, ligne in enumerate(plan):
        y = hauteur - 1 - row_index  # inverse la lecture : (0,0) en bas à gauche comme Arcade
        for x, caractere in enumerate(ligne):
            maze_grid[(x, y)] = caractere
            if caractere == MUR:
                murs.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            elif caractere == MUR_FISSURE:
                murs.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            elif caractere in (PORTE, CLE, FIOLE, LEVIER, SORTIE):
                objets.append((x, y, caractere))

    return maze_grid, murs, objets


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
