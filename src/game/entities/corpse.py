"""Cadavre laisse au sol : element de decor interactif (poids sur dalle, blocage...).

Responsable : Thais
"""
import arcade


class Corpse(arcade.Sprite):
    def __init__(self, position: tuple[float, float]) -> None:
        super().__init__()
        self.position = position
