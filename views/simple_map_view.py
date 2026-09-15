"""Vue de la map simplifiee (branche remodelage-map) : meme style pixel-art et
meme mecanique vivant/fantome que le couloir d'entrainement, sur une salle un peu
plus grande. Pas d'objets, de decor ramassable ni de brume : juste les murs, les
torches, le mur dore et la sortie. HUD en bandeau lateral (pas de bandeau du bas).
"""
import os
import sys
import math
import random
from pathlib import Path

import pygame

from systems.training_level import TrainingLevel
from views.pixel_art import PixelTiles

MAPS_DIR = Path(__file__).resolve().parents[1] / "assets/maps"
MAP_PATH = MAPS_DIR / "sanctuaire_radial.json"

# Positions propres a la geometrie de sanctuaire_radial.json (hub au centre,
# salle Nord tout en haut, salle Sud-Est en bas a droite) : fontaines bleues
# et bassin d'eau, comme sur la reference "Le Sanctuaire des Veilleurs".
HUB_CENTER = (25 * 16 + 8, 25 * 16 + 8)
NORTH_CENTER = (25 * 16 + 8, 8 * 16 + 8)
WATER_RECT = pygame.Rect(35 * 16, 35 * 16, 4 * 16, 4 * 16)

TOP_BAR_H = 20
SIDEBAR_W = 130
PLAY_W, PLAY_H = 340, 330
SIZE = (PLAY_W + SIDEBAR_W, TOP_BAR_H + PLAY_H)
VIEW = pygame.Rect(0, TOP_BAR_H, PLAY_W, PLAY_H)
SIDEBAR = pygame.Rect(PLAY_W, 0, SIDEBAR_W, SIZE[1])

GOLD = (224, 191, 119)
INK = (12, 17, 25)
WHITE = (222, 225, 216)

VISION_ALIVE = 82
VISION_GHOST = 100

GHOST_PALETTE = {".": (0, 0, 0, 0), "w": (235, 238, 240), "W": (196, 202, 208)}
GHOST_ROWS = ["..www..", ".wwwww.", ".wWwWw.", ".wwwww.", ".wwwww.", "w.w.w.w"]


def build_sprite(rows, palette):
    image = pygame.Surface((max(map(len, rows)), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            image.set_at((x, y), palette[char])
    return image


def make_glow(radius, color, strength):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(strength * (1 - r / radius) ** 0.7)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


def draw_fountain(surface, cx, cy):
    """La grande lueur bleue (hub et salle Nord), comme sur la reference."""
    glow = make_glow(46, (90, 190, 220), 200)
    surface.blit(glow, (cx - 46, cy - 46), special_flags=pygame.BLEND_RGBA_ADD)
    for r in (22, 16):
        pygame.draw.circle(surface, (110, 200, 220, 170), (cx, cy), r, 1)
    pygame.draw.rect(surface, (40, 70, 78, 255), (cx - 6, cy - 2, 12, 6), border_radius=2)
    pygame.draw.polygon(surface, (170, 230, 240, 230), [(cx - 3, cy - 2), (cx, cy - 26), (cx + 3, cy - 2)])
    pygame.draw.polygon(surface, (220, 250, 255, 255), [(cx - 1, cy - 2), (cx, cy - 20), (cx + 1, cy - 2)])


def draw_water(surface, rect):
    """La riviere/bassin de la salle Sud-Est."""
    pygame.draw.rect(surface, (30, 70, 85, 235), rect)
    for i in range(4):
        y = rect.y + 8 + i * (rect.h - 16) // 3
        points = [(rect.x + 4 + t, y + math.sin(t * 0.35 + i) * 3) for t in range(0, rect.w - 8, 4)]
        if len(points) > 1:
            pygame.draw.lines(surface, (90, 170, 185, 160), False, points, 1)
    pygame.draw.rect(surface, (55, 110, 120, 255), rect, 1)


def draw_statue(surface, cx, cy):
    """Petite statue de pierre sur son socle, au milieu du bassin."""
    pygame.draw.ellipse(surface, (20, 45, 55, 140), (cx - 10, cy + 4, 20, 6))
    pygame.draw.rect(surface, (60, 68, 78, 255), (cx - 6, cy + 2, 12, 5), border_radius=1)
    pygame.draw.polygon(surface, (120, 130, 140, 255), [(cx - 5, cy + 2), (cx + 5, cy + 2), (cx + 3, cy - 10), (cx - 3, cy - 10)])
    pygame.draw.circle(surface, (135, 145, 155, 255), (cx, cy - 13), 4)


def draw_bush(surface, cx, cy):
    for dx, dy, r in ((-3, 0, 4), (3, 0, 4), (0, -3, 4)):
        pygame.draw.circle(surface, (55, 110, 60, 235), (cx + dx, cy + dy), r)
    pygame.draw.circle(surface, (80, 150, 85, 235), (cx, cy - 2), 3)


def scatter_leaves(surface, level, rate=0.05):
    """Quelques feuilles eparpillees au sol, un peu partout."""
    for y in range(level.height):
        for x in range(level.width):
            if level.tile(x, y) != ".":
                continue
            rng = random.Random((x * 92821) ^ (y * 68917) ^ 51)
            if rng.random() < rate:
                cx = x * 16 + rng.randint(4, 12)
                cy = y * 16 + rng.randint(4, 12)
                color = rng.choice([(90, 140, 70, 230), (70, 120, 60, 230)])
                pygame.draw.ellipse(surface, color, (cx - 2, cy - 1, 4, 2))


def compute_wall_torches(level, spacing=3):
    """Une torche sur chaque face de mur ouverte sur une case franchissable, quelle
    que soit son orientation (haut, bas, ou les deux faces d'un mur separateur)."""
    torches = []
    for y in range(level.height):
        for x in range(level.width):
            if level.tile(x, y) != "#":
                continue
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if level.tile(x + dx, y + dy) == "#":
                    continue
                if (x * 3 + y * 5 + dx * 2 + dy) % spacing != 0:
                    continue
                point = (x * 16 + 8 + dx * 4, y * 16 + 8 + dy * 4)
                if point not in torches:
                    torches.append(point)
    return torches


class SimpleMapGame:
    def __init__(self):
        self.level = TrainingLevel(MAP_PATH)
        self.tiles = PixelTiles(self.level, decorate=False)
        self.torches = compute_wall_torches(self.level)
        self.tiles_ghost_surface = pygame.transform.grayscale(self.tiles.surface)
        self.tiles_ghost_surface.fill((175, 175, 175), special_flags=pygame.BLEND_RGB_ADD)

        map_size = (self.level.width * 16, self.level.height * 16)
        self.decor_surface = pygame.Surface(map_size, pygame.SRCALPHA)
        draw_fountain(self.decor_surface, *HUB_CENTER)
        draw_fountain(self.decor_surface, *NORTH_CENTER)
        draw_water(self.decor_surface, WATER_RECT)
        draw_statue(self.decor_surface, WATER_RECT.centerx, WATER_RECT.centery)
        draw_bush(self.decor_surface, WATER_RECT.x - 6, WATER_RECT.centery + 10)
        draw_bush(self.decor_surface, WATER_RECT.right + 6, WATER_RECT.centery - 10)
        scatter_leaves(self.decor_surface, self.level)
        self.decor_ghost_surface = pygame.transform.grayscale(self.decor_surface)
        self.decor_ghost_surface.fill((175, 175, 175), special_flags=pygame.BLEND_RGB_ADD)

        self.tiles_with_decor = self.tiles.surface.copy()
        self.tiles_with_decor.blit(self.decor_surface, (0, 0))

        self.font = pygame.font.Font(None, 18)
        self.small = pygame.font.Font(None, 14)
        self.ghost_sprite = build_sprite(GHOST_ROWS, GHOST_PALETTE)

        self.map_w = self.level.width * 16
        self.map_h = self.level.height * 16
        # La salle est plus grande que l'ecran de jeu : camera qui suit le joueur,
        # avec sa petite zone eclairee autour de lui. La carte entiere reste
        # consultable via M (draw_map), en net (pas de flou).
        self.camera = pygame.Vector2()
        self.update_camera()

        self.elapsed = 0.0
        self.facing_left = False
        self.moving = False
        self.map_open = False
        self.shade = pygame.Surface(VIEW.size, pygame.SRCALPHA)
        self.lights = {}

        self.special_tiles = []
        for y in range(self.level.height):
            for x in range(self.level.width):
                tile = self.level.tile(x, y)
                if tile in "YE":
                    self.special_tiles.append((x, y, tile))

        self.title_surface = self.font.render("LE SANCTUAIRE DES VEILLEURS", True, GOLD)
        self.inventory_title = self.font.render("INVENTAIRE", True, GOLD)
        self.controls_lines = [
            "ZQSD/Fleches",
            "  bouger",
            "P : potion",
            "M : carte",
            "R : recommencer",
        ]

    def update_camera(self):
        p = self.level.position
        self.camera.x = max(0, min(p.x - VIEW.w / 2, max(0, self.map_w - VIEW.w)))
        self.camera.y = max(0, min(p.y - VIEW.h / 2, max(0, self.map_h - VIEW.h)))

    def label(self, screen, text, position, color=WHITE, font=None):
        screen.blit((font or self.font).render(text, True, color), position)

    def update(self, dt, direction):
        if self.map_open:
            return
        old = self.level.position.copy()
        self.level.update(dt, direction)
        self.moving = old.distance_to(self.level.position) > 0.01
        if direction[0]:
            self.facing_left = direction[0] < 0
        self.elapsed += dt
        self.update_camera()

    def event(self, key):
        if key == pygame.K_m:
            self.map_open = not self.map_open
        elif key == pygame.K_r:
            self.__init__()
        elif not self.map_open:
            self.level.action(key)

    def glow(self, radius, strength):
        key = (radius, strength)
        if key not in self.lights:
            light = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -2):
                alpha = int(strength * (1 - r / radius) ** 0.55)
                pygame.draw.circle(light, (0, 0, 0, alpha), (radius, radius), r)
            self.lights[key] = light
        return self.lights[key]

    def point(self, world_pos):
        return round(world_pos[0] - self.camera.x), round(world_pos[1] - self.camera.y + VIEW.y)

    def draw(self, screen):
        level = self.level
        screen.fill(INK)
        screen.set_clip(VIEW)

        tiles_surface = self.tiles_ghost_surface if level.ghost else self.tiles.surface
        decor_surface = self.decor_ghost_surface if level.ghost else self.decor_surface
        screen.blit(tiles_surface, (-self.camera.x, VIEW.y - self.camera.y))
        screen.blit(decor_surface, (-self.camera.x, VIEW.y - self.camera.y))

        for x, y, tile in self.special_tiles:
            px, py = self.point((x * 16 + 8, y * 16 + 8))
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

        torch_points = [
            (wx, self.point((wx, wy)))
            for wx, wy in self.torches
            if -60 < wx - self.camera.x < VIEW.w + 60 and -60 < wy - self.camera.y < VIEW.h + 60
        ]

        self.shade.fill((4, 7, 15, 210))
        radius = VISION_GHOST if level.ghost else VISION_ALIVE
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
        self.draw_top_bar(screen)
        self.draw_sidebar(screen)
        if self.map_open:
            self.draw_map(screen)
        if level.won:
            self.draw_win(screen)

    def draw_top_bar(self, screen):
        pygame.draw.rect(screen, INK, (0, 0, PLAY_W, TOP_BAR_H))
        screen.blit(self.title_surface, (8, 2))
        pygame.draw.line(screen, (61, 65, 64), (0, TOP_BAR_H - 1), (PLAY_W, TOP_BAR_H - 1))

    def draw_sidebar(self, screen):
        level = self.level
        pygame.draw.rect(screen, INK, SIDEBAR)
        pygame.draw.line(screen, (61, 65, 64), (SIDEBAR.x, 0), (SIDEBAR.x, SIDEBAR.h))

        x = SIDEBAR.x + 8
        y = 8
        screen.blit(self.inventory_title, (x, y))
        y += 20

        status = "AME ERRANTE" if level.ghost else "VIVANT"
        self.label(screen, status, (x, y), (154, 222, 211) if level.ghost else WHITE, self.small)
        y += 14
        self.label(screen, f"Fioles : {level.mode.potions.count}", (x, y), (192, 150, 228), self.small)
        y += 16

        if level.ghost:
            pygame.draw.rect(screen, (43, 48, 63), (x, y, SIDEBAR_W - 16, 4))
            pygame.draw.rect(screen, (172, 136, 223), (x, y, int((SIDEBAR_W - 16) * level.mode.time_remaining / level.mode.duration), 4))
            y += 12

        y += 8
        self.label(screen, "Objets :", (x, y), GOLD, self.small)
        y += 14
        self.label(screen, "-", (x, y), (139, 156, 163), self.small)
        y += 20

        for i, line in enumerate(self.controls_lines):
            self.label(screen, line, (x, SIDEBAR.h - 68 + i * 14), (136, 149, 157), self.small)

    def draw_map(self, screen):
        box = pygame.Rect(15, 15, SIZE[0] - 30, SIZE[1] - 30)
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((6, 10, 16, 210))
        screen.blit(veil, (0, 0))
        pygame.draw.rect(screen, (18, 25, 34), box)
        pygame.draw.rect(screen, (100, 96, 77), box, 1)

        scale = min((box.w - 10) / self.map_w, (box.h - 10) / self.map_h)
        scaled = pygame.transform.scale(self.tiles_with_decor, (round(self.map_w * scale), round(self.map_h * scale)))
        origin = (box.centerx - scaled.get_width() // 2, box.centery - scaled.get_height() // 2)
        screen.blit(scaled, origin)

        cx = origin[0] + round(self.level.position.x * scale)
        cy = origin[1] + round(self.level.position.y * scale)
        pygame.draw.rect(screen, (230, 246, 232), (cx - 3, cy - 3, 6, 6), 1)

        self.label(screen, "CARTE (M pour fermer)", (box.x + 10, box.y + 6), GOLD, self.small)

    def draw_win(self, screen):
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((6, 16, 22, 220))
        screen.blit(veil, (0, 0))
        self.label(screen, "SORTIE ATTEINTE", (SIZE[0] // 2 - 55, SIZE[1] // 2 - 10), GOLD, self.font)
        self.label(screen, "R : recommencer    Echap : quitter", (SIZE[0] // 2 - 90, SIZE[1] // 2 + 10), WHITE, self.small)


def main():
    if "--smoke-test" in sys.argv:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        desktop = pygame.display.Info()
        desktop_size = (desktop.current_w or 1280, desktop.current_h or 720)
        window = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
        pygame.display.set_caption("Le sanctuaire - Deadweight")

        # Plein ecran reel : on remplit tout l'ecran, sans bandes noires.
        canvas = pygame.Surface(SIZE)
        game = SimpleMapGame()
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
            window.blit(pygame.transform.scale(canvas, desktop_size), (0, 0))
            pygame.display.flip()
            if "--smoke-test" in sys.argv:
                running = False
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
