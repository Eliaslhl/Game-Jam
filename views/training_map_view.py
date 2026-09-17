"""Rendu du couloir d'entrainement, meme style pixel-art que le niveau final de Kadir."""
import math
import os
import sys
import textwrap

import pygame

from entities.ghost import YureiWalk
from systems.training_level import TrainingLevel
from views.pixel_art import PixelTiles
from views.pixel_effects import (
    DANGER_COLOR,
    danger_shake,
    draw_danger_vignette,
    ghost_danger_intensity,
    lerp_color,
    make_glow,
)
from settings import (
    DEFEAT_SOUND,
    END_SOUND_VOLUME,
    TITLE_FONT_FILE,
    UI_FONT_FILE,
    TEXT_DIM,
    DIVIDER,
    GHOST_STATUS,
    GHOST_BAR_BG,
    GHOST_BAR_FILL,
    POTION_COUNT,
    VICTORY_SOUND,
)
from views.effects import build_corpse_sprite

SIZE = (320, 150)
VIEW = pygame.Rect(0, 24, 320, 48)
GOLD = (224, 191, 119)
INK = (12, 17, 25)
WHITE = (222, 225, 216)
HOLE_VOID = (18, 10, 28)
HOLE_RIM = (172, 136, 223)
GAME_OVER_RED = (196, 30, 30)
RESURRECTION_COUNT = (150, 200, 228)
DEAD_STATUS = (232, 120, 120)
WIN_VEIL = (6, 16, 22, 220)
LOSS_VEIL = (30, 8, 12, 220)


class TrainingGame:
    def __init__(self, scale=1.0, offset=(0, 0)):
        # Le decor (tuiles, sprites) reste en pixel-art brut, agrandi au nearest
        # neighbor par l'appelant : net et volontairement blocky. Le texte, lui,
        # est rendu directement a la resolution finale de la fenetre (voir
        # draw_text()) pour rester lisse, sans flou ni aspect pixelise.
        self.scale = scale
        self.offset = offset
        # Pas de pieges dans le tutoriel : on decouvre la mecanique fantome sans
        # se faire surprendre, les vrais trous n'apparaissent qu'en partie.
        self.level = TrainingLevel(hole_count=0)
        self.tiles = PixelTiles(self.level)
        self._add_bottom_wall_torches()
        # En mode fantome, le couloir devient presque blanc (le reste garde ses couleurs).
        self.tiles_ghost_surface = pygame.transform.grayscale(self.tiles.surface)
        self.tiles_ghost_surface.fill((175, 175, 175), special_flags=pygame.BLEND_RGB_ADD)
        # Meme police que le menu principal (MedievalSharp) pour le HUD, a la
        # taille finale (voir scale ci-dessus).
        self.font = pygame.font.Font(str(TITLE_FONT_FILE), max(1, round(12 * self.scale)))
        self.small = pygame.font.Font(str(UI_FONT_FILE), max(1, round(9 * self.scale)))
        self.yurei = YureiWalk()
        self.ghost_frames = [pygame.transform.scale(f, (13, 23)) for f in self.yurei.frames]
        self.corpse_sprite = build_corpse_sprite()
        self.elapsed = 0.0
        self.facing_left = False
        self.moving = False
        self.danger_intensity = 0.0
        self.shake_offset = (0.0, 0.0)
        self.end_sounds = self._load_end_sounds()
        self.end_sound_state = None
        self.shade = pygame.Surface(VIEW.size, pygame.SRCALPHA)
        self.lights = {}

        # Le plan ne change jamais : autant reperer une bonne fois les cases 'Y'/'E'
        # plutot que de rescanner toute la grille a chaque frame.
        self.special_tiles = [
            (x, y, tile)
            for y in range(self.level.height)
            for x in range(self.level.width)
            for tile in [self.level.tile(x, y)]
            if tile in "YE"
        ]

        # Textes qui ne changent jamais : rendus une seule fois plutot qu'a chaque
        # frame, deja a la taille finale donc anticrenelage actif (net, sans flou).
        self.title_surface = self.font.render("COULOIR D'ENTRAINEMENT", True, GOLD)
        # Les memes touches que la partie, annoncees avec les memes mots : le
        # tutoriel sert a les apprendre, elles ne doivent pas differer d'un
        # mode a l'autre. Deux lignes car tout ne tient pas sur la largeur.
        self.controls_surfaces = [
            self.small.render(line, True, (136, 149, 157))
            for line in ("ZQSD / fleches : bouger   P ou Entree : fantome / retour",
                         "R : recommencer   Echap : quitter")
        ]

    def _add_bottom_wall_torches(self):
        """PixelTiles ne met des torches que sur le mur du haut : on symetrise en bas."""
        level = self.level
        y = level.height - 1
        for x in range(level.width):
            if level.tile(x, y) == "#" and level.tile(x, y - 1) not in "#Y" and x % 3 == 0:
                point = (x * 16 + 8, y * 16 + 4)
                if point not in self.tiles.torches:
                    self.tiles.torches.append(point)

    def label(self, screen, text, position, color=WHITE, font=None):
        """Rendu direct sur `screen` (deja a la resolution finale) : position
        donnee dans le repere du petit canevas pixel-art, mise a l'echelle ici."""
        surface = (font or self.font).render(text, True, color)
        screen.blit(surface, (position[0] * self.scale + self.offset[0], position[1] * self.scale + self.offset[1]))

    def update(self, dt, direction):
        old = self.level.position.copy()
        self.level.update(dt, direction)
        self._play_end_sound_if_needed()
        self.moving = old.distance_to(self.level.position) > 0.01
        if direction[0]:
            self.facing_left = direction[0] < 0
        self.elapsed += dt

        mode = self.level.mode
        self.danger_intensity = (
            ghost_danger_intensity(mode.time_remaining, mode.duration) if self.level.ghost else 0.0
        )
        self.shake_offset = danger_shake(self.elapsed, self.danger_intensity)

    @staticmethod
    def _load_end_sounds():
        if not pygame.mixer.get_init():
            return {}
        sounds = {}
        for state, path in (("win", VICTORY_SOUND), ("loss", DEFEAT_SOUND)):
            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(END_SOUND_VOLUME)
                sounds[state] = sound
            except (pygame.error, OSError) as error:
                print(f"Son de fin indisponible ({path.name}) : {error}")
        return sounds

    def _play_end_sound_if_needed(self):
        state = "loss" if self.level.lost else "win" if self.level.won else None
        if state == self.end_sound_state:
            return
        if state in self.end_sounds:
            self.end_sounds[state].play()
        self.end_sound_state = state

    def event(self, key):
        # R et N relancent a tout moment, comme en partie (PuzzleGame.event) :
        # dans le tutoriel, R ressuscitait, ce qui apprenait l'inverse du jeu.
        if key in (pygame.K_r, pygame.K_n):
            if pygame.mixer.get_init():
                pygame.mixer.music.unpause()
            self.__init__(scale=self.scale, offset=self.offset)
        else:
            self.level.action(key)

    def point(self, world):
        return round(world[0] + self.shake_offset[0]), round(world[1] + VIEW.y + self.shake_offset[1])

    def glow(self, radius, strength):
        key = (radius, strength)
        if key not in self.lights:
            self.lights[key] = make_glow(radius, (0, 0, 0), strength, exponent=0.55)
        return self.lights[key]

    def draw(self, screen):
        level = self.level
        screen.fill(INK)
        screen.set_clip(VIEW)
        tiles_surface = self.tiles_ghost_surface if level.ghost else self.tiles.surface
        screen.blit(tiles_surface, (0, VIEW.y))
        for x, y, tile in self.special_tiles:
            px, py = self.point(level.center((x, y)))
            if tile == "Y":
                rect = pygame.Rect(px - 8, py - 8, 16, 16)
                pygame.draw.rect(screen, (64, 62, 63), rect.inflate(-1, -1))
                pygame.draw.rect(screen, (129, 108, 58), rect.inflate(-4, -2), 1)
                for offset in (-4, 4):
                    pygame.draw.line(screen, (245, 209, 110), (px + offset, py - 5), (px + offset, py + 5))
                if level.ghost:
                    pygame.draw.line(screen, (155, 239, 226), (px - 2, py - 3), (px + 2, py + 3))
            elif tile == "E":
                pygame.draw.rect(screen, (29, 55, 49), (px - 10, py - 14, 20, 25))
                pygame.draw.rect(screen, (119, 232, 155), (px - 10, py - 14, 20, 25), 2, border_radius=8)
        if level.ghost:
            # Invisibles pour un vivant : ne se revelent qu'en mode fantome.
            for hx, hy in level.holes:
                hpx, hpy = self.point(level.center((hx, hy)))
                pygame.draw.circle(screen, HOLE_VOID, (hpx, hpy), 7)
                pygame.draw.circle(screen, HOLE_RIM, (hpx, hpy), 7, 1)
        corpse = self.corpse_sprite
        for corpse_position in level.mode.corpse_positions:
            cx, cy = self.point(corpse_position)
            screen.blit(corpse, (cx - corpse.get_width() // 2, cy - corpse.get_height() // 2 + 4))
        px, py = self.point(level.position)
        pygame.draw.ellipse(screen, (12, 19, 27), (px - 6, py + 2, 12, 5))
        if level.ghost:
            index = int(self.elapsed / 0.14) % len(self.ghost_frames) if self.moving else 0
            frame = self.ghost_frames[index]
            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (px - 6, py - 19))
        else:
            frame = self.tiles.art["player"]
            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            bob = int(self.elapsed * 8) % 2 if self.moving else 0
            screen.blit(frame, (px - frame.get_width() // 2, py - frame.get_height() + 4 - bob))

        torch_points = [(wx, self.point((wx, wy))) for wx, wy in self.tiles.torches]

        self.shade.fill((4, 7, 15, 210))
        radius = level.vision
        self.shade.blit(self.glow(radius, 235), (px - radius, py - VIEW.y - radius), special_flags=pygame.BLEND_RGBA_SUB)
        for wx, (tx, ty) in torch_points:
            self.shade.blit(self.glow(43, 120), (tx - 43, ty - VIEW.y - 43), special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(self.shade, VIEW.topleft)

        for wx, (px2, py2) in torch_points:
            pygame.draw.rect(screen, (93, 60, 39), (px2 - 2, py2, 4, 6))
            flame = 4 + int(math.sin(self.elapsed * 11 + wx) * 1.5)
            pygame.draw.polygon(screen, (205, 112, 47), [(px2 - 3, py2), (px2, py2 - flame - 3), (px2 + 3, py2)])
            pygame.draw.line(screen, (255, 223, 131), (px2, py2), (px2, py2 - flame))

        if self.danger_intensity:
            draw_danger_vignette(screen, VIEW, self.elapsed, self.danger_intensity)

        screen.set_clip(None)
        self.draw_hud(screen)

    def draw_text(self, screen):
        """Deuxieme passe : tout le texte du HUD, dessine directement a la
        resolution finale de `screen` (net, ni flou ni pixelise), par-dessus le
        petit canevas pixel-art deja agrandi et blitte dessus par l'appelant."""
        level = self.level
        self.draw_hud_text(screen)
        if not (level.won or level.lost):
            return
        # Le voile des ecrans de fin est pose ici, sur l'ecran et apres le HUD,
        # et non sur le canevas : tout ce qui precede - decor et HUD compris -
        # passe ainsi au second plan, seul le message de fin reste en pleine
        # lumiere. Pose sur le canevas, il aurait laisse le texte du HUD briller
        # par-dessus, puisque celui-ci est dessine en dernier.
        veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        veil.fill(WIN_VEIL if level.won else LOSS_VEIL)
        screen.blit(veil, (0, 0))
        if level.won:
            self.draw_win_text(screen)
        else:
            self.draw_loss_text(screen)

    def draw_hud(self, screen):
        """Fond + separateurs uniquement : le texte est dans draw_hud_text()."""
        pygame.draw.rect(screen, INK, (0, 0, SIZE[0], 22))
        pygame.draw.line(screen, DIVIDER, (8, 21), (SIZE[0] - 8, 21))

        pygame.draw.rect(screen, INK, (0, 72, SIZE[0], SIZE[1] - 72))
        pygame.draw.line(screen, DIVIDER, (8, 73), (SIZE[0] - 8, 73))
        level = self.level
        if level.ghost:
            pygame.draw.rect(screen, GHOST_BAR_BG, (70, 80, 80, 4), border_radius=2)
            pygame.draw.rect(screen, GHOST_BAR_FILL, (70, 80, int(80 * level.mode.time_remaining / level.mode.duration), 4), border_radius=2)

    def draw_hud_text(self, screen):
        level = self.level
        screen.blit(self.title_surface, (8 * self.scale + self.offset[0], 5 * self.scale + self.offset[1]))
        # Trois etats, pas deux : sans le cas "mort", l'etat affiche retombe sur
        # "VIVANT" pendant l'ecran de mort (`ghost` y est faux, comme vivant).
        if level.dead or level.lost:
            status, status_color = "MORT", DEAD_STATUS
        elif level.ghost:
            status, status_color = "AME ERRANTE", GHOST_STATUS
        else:
            status, status_color = "VIVANT", WHITE
        self.label(screen, status, (8, 79), status_color, self.small)
        self.label(screen, f"POISON {level.mode.poison_potions.count}", (SIZE[0] - 118, 79), POTION_COUNT, self.small)
        self.label(screen, f"RESUR. {level.mode.resurrection_potions.count}", (SIZE[0] - 118, 93), RESURRECTION_COUNT, self.small)
        message = level.message if level.message_time > 0 else "P ou Entree : fantome / retour. R : recommencer."
        for i, line in enumerate(textwrap.wrap(message, 38)):
            self.label(screen, line, (8, 92 + i * 11), WHITE, self.small)
        for i, surface in enumerate(self.controls_surfaces):
            y = (SIZE[1] - 25 + i * 11) * self.scale + self.offset[1]
            screen.blit(surface, (8 * self.scale + self.offset[0], y))

    def draw_win_text(self, screen):
        self.label(screen, "COULOIR VALIDE", (SIZE[0] // 2 - 45, 55), GOLD, self.font)
        self.label(screen, "N : recommencer    Echap : quitter", (SIZE[0] // 2 - 85, 75), WHITE, self.small)

    def draw_loss_text(self, screen):
        self.label(screen, "VOUS ETES MORT", (SIZE[0] // 2 - 48, 55), DEAD_STATUS, self.font)
        self.label(screen, "N : recommencer    Echap : quitter", (SIZE[0] // 2 - 85, 75), WHITE, self.small)


def run(screen):
    """Boucle du couloir dans une fenetre DEJA ouverte (ex : reprise de la
    fenetre du menu, meme taille). N'appelle ni pygame.init() ni pygame.quit() :
    c'est a l'appelant de gerer le cycle de vie de pygame."""
    target_size = screen.get_size()
    # Le couloir garde ses proportions (pas de deformation) : on l'agrandit au
    # maximum dans la fenetre, avec de fines bandes noires si besoin.
    scale = min(target_size[0] / SIZE[0], target_size[1] / SIZE[1])
    scaled_size = (round(SIZE[0] * scale), round(SIZE[1] * scale))
    offset = ((target_size[0] - scaled_size[0]) // 2, (target_size[1] - scaled_size[1]) // 2)

    canvas = pygame.Surface(SIZE)
    game = TrainingGame(scale=scale, offset=offset)
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = min(clock.tick(60) / 1000, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    game.event(event.key)
        keys = pygame.key.get_pressed()
        direction = (
            int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_q] or keys[pygame.K_LEFT]),
            int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_z] or keys[pygame.K_UP]),
        )
        game.update(dt, direction)
        game.draw(canvas)
        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(canvas, scaled_size), offset)
        game.draw_text(screen)
        pygame.display.flip()
        if "--smoke-test" in sys.argv:
            running = False


def main():
    """Lancement autonome (python views/training_map_view.py) : plein ecran reel,
    sans bandes noires, sans lissage (le rendu doit rester net, pas flou)."""
    if "--smoke-test" in sys.argv:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        desktop = pygame.display.Info()
        desktop_size = (desktop.current_w or 1280, desktop.current_h or 720)
        window = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
        pygame.display.set_caption("Couloir d'entrainement - Deadweight")
        run(window)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
