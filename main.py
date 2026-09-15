from views.training_map_view import main
"""Point d'entree du jeu."""
import arcade

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, load_fonts
from views.menu_view import MenuView

def main() -> None:
    load_fonts()
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MenuView())
    arcade.run()
    return


if __name__ == "__main__":
    main()
