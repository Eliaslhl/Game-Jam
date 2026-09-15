"""Bascule Vivant <-> Fantome : gestion de l'etat courant du joueur.

Responsable : Kadir
"""
from enum import Enum, auto
from systems.potion import PotionInventory
from settings import GHOST_MODE_DURATION


class PlayerState(Enum):
    ALIVE = auto()
    GHOST = auto()


class GhostModeController:
    def __init__(self, duration: float = GHOST_MODE_DURATION) -> None:
        self.state = PlayerState.ALIVE
        self.duration = duration
        self.time_remaining = 0.0
        self.corpse_position = None
        self.potions = PotionInventory()

    def enter_ghost_mode(self, position=(0, 0)) -> bool:
        if self.state is PlayerState.GHOST or not self.potions.drink():
            return False
        self.corpse_position = tuple(position)
        self.state = PlayerState.GHOST
        self.time_remaining = self.duration
        return True

    def return_to_alive(self):
        """Retourne la position du corps pour une resurrection sans collision."""
        self.state = PlayerState.ALIVE
        self.time_remaining = 0.0
        return self.corpse_position

    def update(self, delta_time: float):
        if self.state is PlayerState.GHOST:
            self.time_remaining = max(0.0, self.time_remaining - max(0.0, delta_time))
            if self.time_remaining == 0:
                return self.return_to_alive()
        return None

    def can_pass_wall(self, ghost_passable: bool) -> bool:
        return self.state is PlayerState.GHOST and ghost_passable
