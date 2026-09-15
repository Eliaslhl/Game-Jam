"""Ecran principal de jeu : boucle de mise a jour et de rendu du labyrinthe."""
import arcade

from src.game.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class GameView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        self.player = None
        self.scene = None
        self.physics_engine = None

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.BLACK)
        self.setup()

    def setup(self) -> None:
        """Charge le niveau, cree le joueur, la scene et le moteur physique."""

    def on_draw(self) -> None:
        self.clear()

    def on_update(self, delta_time: float) -> None:
        pass

    def on_key_press(self, key: int, modifiers: int) -> None:
        pass

    def on_key_release(self, key: int, modifiers: int) -> None:
        pass
