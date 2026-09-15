"""Point d'entree du jeu."""
import arcade

from src.game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from src.game.views.menu_view import MenuView


def main() -> None:
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()
