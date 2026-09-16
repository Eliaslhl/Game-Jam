import os
import sys

import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_TITLE,
    UI_FONT_FILE,
    TITLE_FONT_FILE,
    BACKGROUND_MUSIC,
    BACKGROUND_MUSIC_VOLUME,
    LOGO_FILE,
    INK,
    PALE,
    GOLD,
    GHOST_BAR_BG,
    KEY_TILE_BG,
    TEXT_DIM,
)
from views import training_map_view
from views import puzzle_view

MENU_ITEMS = [
    ("Jouer", "play"),
    ("Tutoriel", "tutorial"),
    ("Quitter", "quit"),
]

BUTTON_WIDTH = 250
BUTTON_HEIGHT = 56
BUTTON_GAP = 16

# Cote du logo (il est carre) : assez grand pour que "Witch or Ghost" reste
# lisible dedans, assez petit pour laisser respirer les boutons en dessous.
LOGO_SIZE = 220
LOGO_GAP = 28


def _load_logo(size: int):
    """Logo du jeu, detoure et mis a l'echelle. Le fichier est un JPEG (donc
    sans transparence) alors que le dessin, lui, est rond : ses coins noirs
    sont retires par un masque circulaire pour qu'il se pose proprement sur le
    fond du menu. Renvoie None si l'image manque (repli sur le titre ecrit)."""
    try:
        image = pygame.image.load(str(LOGO_FILE)).convert()
    except (pygame.error, OSError):
        return None

    logo = pygame.Surface((size, size), pygame.SRCALPHA)
    logo.blit(pygame.transform.smoothscale(image, (size, size)), (0, 0))

    # Masque dessine en plus grand puis reduit : pygame.draw.circle ne fait pas
    # d'anticrenelage, ce detour donne un bord de disque net mais pas crenele.
    supersample = 4
    big = size * supersample
    mask = pygame.Surface((big, big), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (big // 2, big // 2), big // 2)
    logo.blit(
        pygame.transform.smoothscale(mask, (size, size)),
        (0, 0),
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    return logo


class Button:
    def __init__(self, label: str, action: str, rect: pygame.Rect) -> None:
        self.label = label
        self.action = action
        self.rect = rect
        self.hovered = False
        self.pressed = False

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = self.hovered
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            triggered = self.pressed and self.hovered
            self.pressed = False
            if triggered:
                return self.action
        return None

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        if self.pressed and self.hovered:
            bg, fg, border = PALE, INK, GOLD
        elif self.hovered:
            bg, fg, border = KEY_TILE_BG, (255, 255, 255), GOLD
        else:
            bg, fg, border = GHOST_BAR_BG, PALE, None

        pygame.draw.rect(screen, bg, self.rect, border_radius=4)
        if border is not None:
            pygame.draw.rect(screen, border, self.rect, width=2, border_radius=4)

        text_surface = font.render(self.label, True, fg)
        screen.blit(text_surface, text_surface.get_rect(center=self.rect.center))


class MenuScene:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title_font = pygame.font.Font(str(TITLE_FONT_FILE), 48)
        self.button_font = pygame.font.Font(str(UI_FONT_FILE), 20)

        # Le logo remplace le titre ecrit ; celui-ci ne sert plus que de repli
        # si l'image n'est pas la (clone du depot sans les assets, par exemple).
        self.logo = _load_logo(LOGO_SIZE)

        # Logo et boutons forment un seul bloc, centre verticalement avec un
        # leger decalage vers le haut : le regard tombe d'abord sur le logo.
        buttons_height = len(MENU_ITEMS) * BUTTON_HEIGHT + (len(MENU_ITEMS) - 1) * BUTTON_GAP
        block_height = LOGO_SIZE + LOGO_GAP + buttons_height
        block_top = (SCREEN_HEIGHT - block_height) // 2 - 36
        logo_center_y = block_top + LOGO_SIZE // 2
        first_button_center_y = block_top + LOGO_SIZE + LOGO_GAP + BUTTON_HEIGHT // 2

        self.logo_rect = None
        self.title_surface = None
        self.title_rect = None
        if self.logo is not None:
            self.logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, logo_center_y))
        else:
            self.title_surface = self.title_font.render("Witch or Ghost", True, GOLD)
            self.title_rect = self.title_surface.get_rect(center=(SCREEN_WIDTH // 2, logo_center_y))

        self.buttons = []
        for i, (label, action) in enumerate(MENU_ITEMS):
            rect = pygame.Rect(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT)
            rect.center = (SCREEN_WIDTH // 2, first_button_center_y + i * (BUTTON_HEIGHT + BUTTON_GAP))
            self.buttons.append(Button(label, action, rect))

    def handle_event(self, event: pygame.event.Event) -> str | None:
        for button in self.buttons:
            action = button.handle_event(event)
            if action is not None:
                return action
        return None

    def draw(self) -> None:
        self.screen.fill(INK)
        if self.logo is not None:
            self.screen.blit(self.logo, self.logo_rect)
        else:
            self.screen.blit(self.title_surface, self.title_rect)
        for button in self.buttons:
            button.draw(self.screen, self.button_font)


def _new_window() -> pygame.Surface:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(SCREEN_TITLE)
    return screen


def _fullscreen_window() -> pygame.Surface:
    """Fenetre plein ecran reel (sans bandes du bureau), pour la partie et le
    tutoriel uniquement : le menu, lui, reste dans sa fenetre normale."""
    desktop = pygame.display.Info()
    desktop_size = (desktop.current_w or SCREEN_WIDTH, desktop.current_h or SCREEN_HEIGHT)
    screen = pygame.display.set_mode(desktop_size, pygame.FULLSCREEN)
    return screen


def run(screen: pygame.Surface) -> None:
    clock = pygame.time.Clock()
    scene = MenuScene(screen)

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            action = scene.handle_event(event)
            if action == "play":
                # Plein ecran pour la partie, puis retour a la fenetre du menu.
                fullscreen = _fullscreen_window()
                if puzzle_view.run(fullscreen) == 'quit':
                    return
                screen = _new_window()
                scene = MenuScene(screen)
            elif action == "tutorial":
                # Plein ecran pour le tutoriel, puis retour a la fenetre du menu.
                fullscreen = _fullscreen_window()
                training_map_view.run(fullscreen)
                screen = _new_window()
                scene = MenuScene(screen)
            elif action == "quit":
                return

        scene.draw()
        pygame.display.flip()
        if "--smoke-test" in sys.argv:
            return


def main() -> None:
    if "--smoke-test" in sys.argv:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    music_started = False
    try:
        try:
            pygame.mixer.music.load(str(BACKGROUND_MUSIC))
            pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
            music_started = True
        except (pygame.error, OSError) as error:
            print(f"Musique indisponible : {error}")

        screen = _new_window()
        run(screen)
    finally:
        if music_started:
            pygame.mixer.music.stop()
        pygame.quit()


if __name__ == "__main__":
    main()
