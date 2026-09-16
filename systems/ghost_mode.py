"""Bascule Vivant <-> Fantome : gestion de l'etat courant du joueur.

Responsable : Kadir
"""
from enum import Enum, auto
from systems.potion import PotionInventory
from settings import GHOST_MODE_DURATION, POISON_VIAL_START_COUNT, RESURRECTION_VIAL_START_COUNT


class PlayerState(Enum):
    ALIVE = auto()
    GHOST = auto()
    DEAD = auto()


class GhostModeController:
    def __init__(self, duration: float = GHOST_MODE_DURATION, *, auto_return_on_timeout: bool = False) -> None:
        self.state = PlayerState.ALIVE
        self.duration = duration
        self.auto_return_on_timeout = auto_return_on_timeout
        self.time_remaining = 0.0
        self.corpse_position = None
        # Deux fioles distinctes : le poison fait mourir (-> fantome), la
        # resurrection ramene a la vie. Independantes l'une de l'autre.
        self.poison_potions = PotionInventory(POISON_VIAL_START_COUNT)
        self.resurrection_potions = PotionInventory(RESURRECTION_VIAL_START_COUNT)

    def enter_ghost_mode(self, position=(0, 0)) -> bool:
        if self.state is PlayerState.GHOST or not self.poison_potions.drink():
            return False
        self.corpse_position = tuple(position)
        self.state = PlayerState.GHOST
        self.time_remaining = self.duration
        return True

    def return_to_alive(self, position=None, *, consume_potion=True):
        """Ressuscite a la position actuelle du fantome si possible."""
        if self.state is not PlayerState.GHOST:
            return None
        if consume_potion and not self.resurrection_potions.drink():
            return None
        self.state = PlayerState.ALIVE
        self.time_remaining = 0.0
        return self.corpse_position if position is None else position

    def die(self):
        self.state = PlayerState.DEAD
        self.time_remaining = 0.0
        return self.corpse_position

    def update(self, delta_time: float):
        if self.state is PlayerState.GHOST:
            self.time_remaining = max(0.0, self.time_remaining - max(0.0, delta_time))
            if self.time_remaining == 0:
                if self.auto_return_on_timeout:
                    return self.return_to_alive(consume_potion=False)
                return self.die()
        return None

    def can_pass_wall(self, ghost_passable: bool) -> bool:
        return self.state is PlayerState.GHOST and ghost_passable

    @property
    def potions(self) -> PotionInventory:
        """Alias retro-compatible vers les fioles de poison, pour le niveau final
        de Kadir (`final_level.py`) qui utilise encore un seul pool partage."""
        return self.poison_potions
