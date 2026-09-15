"""Representation du labyrinthe : murs, portes, clefs, zones secretes.

Responsable : Melissa
"""


class Maze:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.walls: list = []
        self.ghost_walls: list = []
        self.doors: list = []
        self.keys: list = []
