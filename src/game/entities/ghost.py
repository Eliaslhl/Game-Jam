"""Forme Fantome du joueur : traversee des murs speciaux, jauge de temps.

Responsable : Kadir
"""
import arcade

from src.game.settings import GHOST_MODE_DURATION, GHOST_MODE_SPEED


class Ghost(arcade.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.speed = GHOST_MODE_SPEED
        self.time_remaining = GHOST_MODE_DURATION

    def update(self, delta_time: float = 1 / 60) -> None:
        self.time_remaining -= delta_time

    def can_pass_wall(self, wall) -> bool:
        """Renvoie True si ce mur specifique (lumiere jaune) est traversable."""
        return False
