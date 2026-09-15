"""Ecran de menu principal."""
import arcade

from src.game.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class MenuView(arcade.View):
    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self) -> None:
        self.clear()
        arcade.draw_text(
            "Deadweight",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            font_size=40,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int) -> None:
        if key == arcade.key.ENTER:
            from src.game.views.game_view import GameView

            self.window.show_view(GameView())
