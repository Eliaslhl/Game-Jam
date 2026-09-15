"""Forme Vivante du joueur : deplacement, collisions, PV, mort.

Responsable : Thais
"""
import arcade

from src.game.settings import PLAYER_MAX_HP, PLAYER_SPEED


class Player(arcade.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.hp = PLAYER_MAX_HP
        self.speed = PLAYER_SPEED
        self.keys_collected: list[str] = []

    def update(self, delta_time: float = 1 / 60) -> None:
        pass

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self) -> None:
        """Le joueur meurt : laisse un cadavre et bascule en mode Fantome."""
