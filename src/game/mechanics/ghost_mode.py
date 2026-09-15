"""Bascule Vivant <-> Fantome : gestion de l'etat courant du joueur.

Responsable : Kadir
"""
from enum import Enum, auto


class PlayerState(Enum):
    ALIVE = auto()
    GHOST = auto()


class GhostModeController:
    def __init__(self) -> None:
        self.state = PlayerState.ALIVE

    def enter_ghost_mode(self) -> None:
        self.state = PlayerState.GHOST

    def return_to_alive(self) -> None:
        self.state = PlayerState.ALIVE
