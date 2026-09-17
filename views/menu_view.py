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

# Proportions du menu, exprimees pour une hauteur d'ecran de reference de 720 px
# (voir MenuScene : tout est remis a l'echelle de l'ecran reel, le menu etant
# maintenant en plein ecran et donc a une resolution qui varie d'une machine a
# l'autre). Le logo est carre ; sa taille est choisie pour que "Witch or Ghost"
# reste lisible dedans sans ecraser les boutons.
REFERENCE_HEIGHT = 720
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 56
BUTTON_GAP = 16
LOGO_SIZE = 220
LOGO_GAP = 28
TITLE_FONT_SIZE = 48
BUTTON_FONT_SIZE = 20


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
        # Le menu est en plein ecran : sa taille depend de la machine, donc tout
        # est dimensionne a partir de la hauteur reelle plutot qu'en pixels fixes.
        # La largeur ne sert qu'a centrer, pour que le menu garde les memes
        # proportions en 16/9 comme en 16/10 ou en ultra-large.
        width, height = screen.get_size()
        scale = height / REFERENCE_HEIGHT

        def px(value: int) -> int:
            return max(1, round(value * scale))

        self.title_font = pygame.font.Font(str(TITLE_FONT_FILE), px(TITLE_FONT_SIZE))
        self.button_font = pygame.font.Font(str(UI_FONT_FILE), px(BUTTON_FONT_SIZE))

        logo_size = px(LOGO_SIZE)
        button_w, button_h = px(BUTTON_WIDTH), px(BUTTON_HEIGHT)
        button_gap, logo_gap = px(BUTTON_GAP), px(LOGO_GAP)

        # Le logo remplace le titre ecrit ; celui-ci ne sert plus que de repli
        # si l'image n'est pas la (clone du depot sans les assets, par exemple).
        self.logo = _load_logo(logo_size)

        # Logo et boutons forment un seul bloc, centre verticalement avec un
        # leger decalage vers le haut : le regard tombe d'abord sur le logo.
        buttons_height = len(MENU_ITEMS) * button_h + (len(MENU_ITEMS) - 1) * button_gap
        block_height = logo_size + logo_gap + buttons_height
        block_top = (height - block_height) // 2 - px(36)
        logo_center_y = block_top + logo_size // 2
        first_button_center_y = block_top + logo_size + logo_gap + button_h // 2

        self.logo_rect = None
        self.title_surface = None
        self.title_rect = None
        if self.logo is not None:
            self.logo_rect = self.logo.get_rect(center=(width // 2, logo_center_y))
        else:
            self.title_surface = self.title_font.render("Witch or Ghost", True, GOLD)
            self.title_rect = self.title_surface.get_rect(center=(width // 2, logo_center_y))

        self.buttons = []
        for i, (label, action) in enumerate(MENU_ITEMS):
            rect = pygame.Rect(0, 0, button_w, button_h)
            rect.center = (width // 2, first_button_center_y + i * (button_h + button_gap))
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


def _fullscreen_window() -> pygame.Surface:
    """Fenetre plein ecran reel (sans bandes du bureau). Tout le jeu s'y tient
    desormais : le menu comme la partie et le tutoriel, donc plus aucun
    changement de resolution entre les deux."""
    desktop = pygame.display.Info()
    desktop_size = (desktop.current_w or SCREEN_WIDTH, desktop.current_h or SCREEN_HEIGHT)
    screen = pygame.display.set_mode(desktop_size, pygame.FULLSCREEN)
    pygame.display.set_caption(SCREEN_TITLE)
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
                if puzzle_view.run(screen) == 'quit':
                    return
                if pygame.mixer.get_init():
                    pygame.mixer.music.unpause()
                # La partie a pu changer de resolution (F11) : on reprend la
                # fenetre courante et on recalcule la mise en page dessus.
                screen = _fullscreen_window()
                scene = MenuScene(screen)
            elif action == "tutorial":
                training_map_view.run(screen)
                if pygame.mixer.get_init():
                    pygame.mixer.music.unpause()
                screen = _fullscreen_window()
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

        screen = _fullscreen_window()
        run(screen)
    finally:
        if music_started:
            pygame.mixer.music.stop()
        pygame.quit()


if __name__ == "__main__":
    main()
