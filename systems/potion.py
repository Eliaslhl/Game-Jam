"""Fioles de poison : consommation volontaire pour declencher le mode Fantome.

Responsable : Kadir
"""
from settings import LIFE_VIAL_START_COUNT, POISON_VIAL_START_COUNT


class PotionInventory:
    def __init__(
        self,
        poison_count: int = POISON_VIAL_START_COUNT,
        life_count: int = LIFE_VIAL_START_COUNT,
    ) -> None:
        self.poison_count = poison_count
        self.life_count = life_count

    def drink_poison(self) -> bool:
        if self.poison_count <= 0:
            return False
        self.poison_count -= 1
        return True

    def drink_life(self) -> bool:
        if self.life_count <= 0:
            return False
        self.life_count -= 1
        return True
