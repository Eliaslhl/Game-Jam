"""Pieges du labyrinthe (jets de flammes, dalles de pression, fleches...)."""
import arcade


class Trap(arcade.Sprite):
    def __init__(self, damage: int = 20) -> None:
        super().__init__()
        self.damage = damage
        self.is_active = True

    def trigger(self, target) -> None:
        pass


class PressurePlate(arcade.Sprite):
    """Dalle qui peut etre bloquee par le poids d'un cadavre."""

    def __init__(self, linked_mechanism_id: str) -> None:
        super().__init__()
        self.linked_mechanism_id = linked_mechanism_id
        self.is_pressed = False
