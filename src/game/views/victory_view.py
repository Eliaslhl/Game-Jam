"""Ecran de victoire affiche a la fin d'un niveau/du jeu."""
import arcade

from src.game.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class VictoryView(arcade.View):
    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.DARK_GREEN)

    def on_draw(self) -> None:
        self.clear()
        arcade.draw_text(
            "Victoire !",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            font_size=40,
            anchor_x="center",
        )
