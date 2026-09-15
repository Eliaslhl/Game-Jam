"""Fioles de poison : consommation volontaire pour declencher le mode Fantome.

Responsable : Kadir
"""
from src.game.settings import POISON_VIAL_START_COUNT


class PotionInventory:
    def __init__(self, count: int = POISON_VIAL_START_COUNT) -> None:
        self.count = count

    def can_drink(self) -> bool:
        return self.count > 0

    def drink(self) -> bool:
        if not self.can_drink():
            return False
        self.count -= 1
        return True
