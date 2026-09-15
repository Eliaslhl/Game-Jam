"""Classe de base pour les ennemis (comportement different selon Vivant/Fantome)."""
import arcade


class BaseEnemy(arcade.Sprite):
    def __init__(self, damage: int = 10) -> None:
        super().__init__()
        self.damage = damage

    def update(self, delta_time: float = 1 / 60) -> None:
        pass
