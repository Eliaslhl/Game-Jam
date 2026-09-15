"""Rendu du couloir d'entrainement, meme style pixel-art que le niveau final de Kadir."""
import math
import os
import sys
import textwrap

import pygame

from systems.training_level import TrainingLevel
from views.pixel_art import PixelTiles

SIZE = (320, 150)
VIEW = pygame.Rect(0, 24, 320, 48)
GOLD = (224, 191, 119)
INK = (12, 17, 25)
WHITE = (222, 225, 216)

# Petit fantome ASCII local (pas d'asset Yurei sur cette branche) : meme technique
# que pixel_art.ascii_sprite, palette a part pour ne pas toucher au fichier partage.
GHOST_PALETTE = {".": (0, 0, 0, 0), "w": (235, 238, 240), "W": (196, 202, 208)}
GHOST_ROWS = ["..www..", ".wwwww.", ".wWwWw.", ".wwwww.", ".wwwww.", "w.w.w.w"]


def build_sprite(rows, palette):
    image = pygame.Surface((max(map(len, rows)), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            image.set_at((x, y), palette[char])
    return image


class TrainingGame:
    def __init__(self):
        self.level = TrainingLevel()
        self.tiles = PixelTiles(self.level)
        self._add_bottom_wall_torches()
        # En mode fantome, le couloir devient presque blanc (le reste garde ses couleurs).
        self.tiles_ghost_surface = pygame.transform.grayscale(self.tiles.surface)
        self.tiles_ghost_surface.fill((175, 175, 175), special_flags=pygame.BLEND_RGB_ADD)
        self.font = pygame.font.Font(None, 18)
        self.small = pygame.font.Font(None, 15)
        self.ghost_sprite = build_sprite(GHOST_ROWS, GHOST_PALETTE)
        self.elapsed = 0.0
        self.facing_left = False
        self.moving = False
        self.shade = pygame.Surface(VIEW.size, pygame.SRCALPHA)
        self.lights = {}

        # Le plan ne change jamais : autant reperer une bonne fois les cases 'Y'/'E'
        # plutot que de rescanner toute la grille a chaque frame.
        self.special_tiles = []
        for y in range(self.level.height):
            for x in range(self.level.width):
                tile = self.level.tile(x, y)
                if tile in "YE":
                    self.special_tiles.append((x, y, tile))

        # Textes qui ne changent jamais : rendus une seule fois plutot qu'a chaque frame.
        self.title_surface = self.font.render("COULOIR D'ENTRAINEMENT", True, GOLD)
        self.controls_surface = self.small.render(
            "ZQSD / fleches : bouger   P : potion   R : recommencer", True, (136, 149, 157)
        )

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
        screen.blit((font or self.font).render(text, True, color), position)

    def update(self, dt, direction):
        old = self.level.position.copy()
        self.level.update(dt, direction)
        self.moving = old.distance_to(self.level.position) > 0.01
        if direction[0]:
            self.facing_left = direction[0] < 0
        self.elapsed += dt

    def event(self, key):
        if key == pygame.K_r:
            self.__init__()
        else:
            self.level.action(key)

    def point(self, world):
        return round(world[0]), round(world[1] + VIEW.y)

    def glow(self, radius, strength):
        key = (radius, strength)
        if key not in self.lights:
            light = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -2):
                alpha = int(strength * (1 - r / radius) ** 0.55)
                pygame.draw.circle(light, (0, 0, 0, alpha), (radius, radius), r)
            self.lights[key] = light
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
        if level.mode.corpse_position is not None:
            cx, cy = self.point(level.mode.corpse_position)
            pygame.draw.ellipse(screen, (118, 105, 109), (cx - 6, cy - 2, 12, 5))
        px, py = self.point(level.position)
        pygame.draw.ellipse(screen, (12, 19, 27), (px - 6, py + 2, 12, 5))
        if level.ghost:
            frame = self.ghost_sprite
            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (px - 4, py - 10))
        else:
            frame = self.tiles.art["player"]
            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (px - 5, py - 8 - (int(self.elapsed * 8) % 2 if self.moving else 0)))

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

        screen.set_clip(None)
        self.draw_hud(screen)
        if level.won:
            self.draw_win(screen)

    def draw_hud(self, screen):
        level = self.level
        pygame.draw.rect(screen, INK, (0, 0, SIZE[0], 22))
        screen.blit(self.title_surface, (8, 5))
        pygame.draw.line(screen, (61, 65, 64), (8, 21), (SIZE[0] - 8, 21))

        pygame.draw.rect(screen, INK, (0, 72, SIZE[0], SIZE[1] - 72))
        pygame.draw.line(screen, (61, 65, 64), (8, 73), (SIZE[0] - 8, 73))
        status = "AME ERRANTE" if level.ghost else "VIVANT"
        self.label(screen, status, (8, 79), (154, 222, 211) if level.ghost else WHITE, self.small)
        self.label(screen, f"POISON {level.mode.poison_potions.count}", (SIZE[0] - 118, 79), (192, 150, 228), self.small)
        self.label(screen, f"RESUR. {level.mode.resurrection_potions.count}", (SIZE[0] - 118, 93), (150, 200, 228), self.small)
        if level.ghost:
            pygame.draw.rect(screen, (43, 48, 63), (70, 80, 80, 4))
            pygame.draw.rect(screen, (172, 136, 223), (70, 80, int(80 * level.mode.time_remaining / level.mode.duration), 4))
        message = level.message if level.message_time > 0 else "P : devenir fantome / redevenir humain"
        for i, line in enumerate(textwrap.wrap(message, 60)):
            self.label(screen, line, (8, 92 + i * 11), WHITE, self.small)
        screen.blit(self.controls_surface, (8, SIZE[1] - 14))

    def draw_win(self, screen):
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((6, 16, 22, 220))
        screen.blit(veil, (0, 0))
        self.label(screen, "COULOIR VALIDE", (SIZE[0] // 2 - 45, 55), GOLD, self.font)
        self.label(screen, "R : recommencer    Echap : quitter", (SIZE[0] // 2 - 85, 75), WHITE, self.small)


def main():
    if "--smoke-test" in sys.argv:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        desktop = pygame.display.Info()
        desktop_size = (desktop.current_w or 1280, desktop.current_h or 720)
        window = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
        pygame.display.set_caption("Couloir d'entrainement - Deadweight")

        # Plein ecran fenetre : pas de changement de mode video, juste une fenetre
        # sans bordure a la taille du bureau. Le rendu garde son ratio (letterbox).
        scale = min(desktop_size[0] / SIZE[0], desktop_size[1] / SIZE[1])
        scaled_size = (round(SIZE[0] * scale), round(SIZE[1] * scale))
        offset = ((desktop_size[0] - scaled_size[0]) // 2, (desktop_size[1] - scaled_size[1]) // 2)

        canvas = pygame.Surface(SIZE)
        game = TrainingGame()
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
            window.fill((0, 0, 0))
            window.blit(pygame.transform.smoothscale(canvas, scaled_size), offset)
            pygame.display.flip()
            if "--smoke-test" in sys.argv:
                running = False
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
