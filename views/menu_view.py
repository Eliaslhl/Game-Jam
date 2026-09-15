"""Écran de menu principal."""
import arcade
import arcade.gui

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BACKGROUND,
    PARCHMENT,
    TITLE,
    WOOD,
    WOOD_LIGHT,
    DIM,
    FONT_TITLE,
    FONT_UI,
)

MENU_ITEMS = ["Jouer", "Tutoriel", "Règles", "Quitter"]


def button_style() -> dict:
    base = dict(font_size=20, font_name=FONT_UI, border_width=2)
    return {
        "normal": arcade.gui.UIFlatButton.UIStyle(
            **base, font_color=PARCHMENT, bg=WOOD, border=(0, 0, 0, 0)
        ),
        "hover": arcade.gui.UIFlatButton.UIStyle(
            **base, font_color=arcade.color.WHITE, bg=WOOD_LIGHT, border=TITLE
        ),
        "press": arcade.gui.UIFlatButton.UIStyle(
            **base, font_color=(20, 16, 12), bg=PARCHMENT, border=TITLE
        ),
        "disabled": arcade.gui.UIFlatButton.UIStyle(
            **base, font_color=DIM, bg=(40, 36, 32), border=(0, 0, 0, 0)
        ),
    }


class MenuView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        self.manager = arcade.gui.UIManager()

        self.title_text = arcade.Text(
            "Deadweight",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 150,
            TITLE,
            font_size=48,
            anchor_x="center",
            font_name=FONT_TITLE,
        )

        style = button_style()
        v_box = arcade.gui.UIBoxLayout(space_between=16)

        actions = {
            "Jouer": self.on_click_play,
            "Tutoriel": self.on_click_tutorial,
            "Règles": self.on_click_rules,
            "Quitter": self.on_click_quit,
        }
        for label, callback in actions.items():
            button = arcade.gui.UIFlatButton(
                text=label, width=250, height=56, style=style
            )
            button.on_click = callback
            v_box.add(button)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=v_box, anchor_x="center_x", anchor_y="center_y", align_y=-40)
        self.manager.add(anchor)

    def on_show_view(self) -> None:
        arcade.set_background_color(BACKGROUND)
        self.manager.enable()

    def on_hide_view(self) -> None:
        self.manager.disable()

    def on_draw(self) -> None:
        self.clear()
        self.title_text.draw()

        self.manager.draw()

    def on_click_play(self, event) -> None:
        print("Zaizai")

    def on_click_tutorial(self, event) -> None:
        print("Zouzou")

    def on_click_rules(self, event) -> None:
        print("Zonzon")

    def on_click_quit(self, event) -> None:
        arcade.exit()
