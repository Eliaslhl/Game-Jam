"""Vue du Sanctuaire des Veilleurs : boucle de jeu, camera, HUD et rendu.
Le decor statique (fontaines, salles thematiques) vit dans `map_theme.py`, les
effets dynamiques (ames errantes, transformation) dans `effects.py`, et les
petits utilitaires de rendu partages avec le couloir d'entrainement dans
`pixel_effects.py`.
"""
import os
import sys
import math
from pathlib import Path

import pygame

from entities.ghost import YureiWalk
from systems.training_level import TrainingLevel
from views.pixel_art import PixelTiles
from views.pixel_effects import make_glow
from views.map_theme import (
    ROOM_RECTS,
    ROOM_THEMES,
    build_ghost_secrets,
    build_room_decor,
    compute_wall_torches,
    flame_colors,
    ghostly,
    room_at,
)
from views.effects import (
    DUST_COLOR,
    DUST_DISPERSE_RADIUS,
    DUST_DISPERSE_STRENGTH,
    SMOKE_COLOR,
    TransformEffect,
    build_soul_sprite,
    generate_dust_motes,
    make_souls,
)

MAPS_DIR = Path(__file__).resolve().parents[1] / "assets/maps"
MAP_PATH = MAPS_DIR / "sanctuaire_radial.json"

TOP_BAR_H = 32
SIDEBAR_W = 130
PLAY_W, PLAY_H = 340, 330
SIZE = (PLAY_W + SIDEBAR_W, TOP_BAR_H + PLAY_H)
VIEW = pygame.Rect(0, TOP_BAR_H, PLAY_W, PLAY_H)
SIDEBAR = pygame.Rect(PLAY_W, 0, SIDEBAR_W, SIZE[1])

GOLD = (224, 191, 119)
INK = (12, 17, 25)
WHITE = (222, 225, 216)

VISION_ALIVE = 62
VISION_GHOST = 62


class SimpleMapGame:
    def __init__(self):
        self.level = TrainingLevel(MAP_PATH)
        self.tiles = PixelTiles(self.level, decorate=False)
        self.torches = compute_wall_torches(self.level)
        self.tiles_ghost_surface = ghostly(self.tiles.surface)

        map_size = (self.level.width * 16, self.level.height * 16)
        self.decor_surface = pygame.Surface(map_size, pygame.SRCALPHA)
        build_room_decor(self.decor_surface, self.tiles, self.level)
        self.decor_ghost_surface = ghostly(self.decor_surface)
        self.ghost_secrets_surface = build_ghost_secrets(map_size)

        self.tiles_with_decor = self.tiles.surface.copy()
        self.tiles_with_decor.blit(self.decor_surface, (0, 0))

        self.dust_motes = generate_dust_motes(self.level, room_at)

        self.font = pygame.font.Font(None, 18)
        self.small = pygame.font.Font(None, 14)
        self.yurei = YureiWalk()
        self.ghost_frames = [pygame.transform.scale(f, (13, 23)) for f in self.yurei.frames]
        self.soul_sprite = build_soul_sprite()
        self.souls = make_souls()
        self.transform_effect = None
        self.was_ghost = False

        self.map_w, self.map_h = map_size
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

        self.special_tiles = [
            (x, y, tile)
            for y in range(self.level.height)
            for x in range(self.level.width)
            for tile in [self.level.tile(x, y)]
            if tile in "YEKD"
        ]
        self.key_glow = make_glow(14, (235, 196, 90), 130)

        self.title_surface = self.font.render("LE SANCTUAIRE DES VEILLEURS", True, GOLD)
        self.zone_labels = {
            name: self.small.render(label, True, (139, 156, 163)) for name, label in ROOM_THEMES.items()
        }
        self.zone_labels[None] = self.small.render("Les Galeries", True, (139, 156, 163))
        self.inventory_title = self.small.render("INVENTAIRE", True, GOLD)

    def current_room(self):
        p = self.level.position
        return room_at(p.x, p.y)

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
        for soul in self.souls:
            soul.update(dt)

        # Le changement d'etat peut venir d'ici (fin du timer) ou d'un appel a
        # event() entre deux frames (touche P) : on compare a l'etat memorise.
        if self.level.ghost != self.was_ghost:
            spot = self.level.mode.corpse_position if self.level.ghost else self.level.position
            self.transform_effect = TransformEffect(spot, expanding=self.level.ghost)
            self.was_ghost = self.level.ghost
        if self.transform_effect:
            self.transform_effect.update(dt)
            if self.transform_effect.done:
                self.transform_effect = None

    def event(self, key):
        if key == pygame.K_m:
            self.map_open = not self.map_open
        elif key == pygame.K_n and (self.level.won or self.level.lost):
            self.__init__()
        elif not self.map_open:
            self.level.action(key)

    def glow(self, radius, strength):
        key = (radius, strength)
        if key not in self.lights:
            self.lights[key] = make_glow(radius, (0, 0, 0), strength, exponent=0.55)
        return self.lights[key]

    def point(self, world_pos):
        return round(world_pos[0] - self.camera.x), round(world_pos[1] - self.camera.y + VIEW.y)

    def draw(self, screen):
        level = self.level
        screen.fill(INK)
        screen.set_clip(VIEW)

        tiles_surface = self.tiles_ghost_surface if level.ghost else self.tiles.surface
        decor_surface = self.decor_ghost_surface if level.ghost else self.decor_surface
        offset = (-self.camera.x, VIEW.y - self.camera.y)
        screen.blit(tiles_surface, offset)
        screen.blit(decor_surface, offset)
        if level.ghost:
            screen.blit(self.ghost_secrets_surface, offset)
            self.draw_souls(screen)

        self.draw_special_tiles(screen, level)

        if level.mode.corpse_position is not None:
            cx, cy = self.point(level.mode.corpse_position)
            pygame.draw.ellipse(screen, (118, 105, 109), (cx - 6, cy - 2, 12, 5))

        px, py = self.point(level.position)
        self.draw_player(screen, level, px, py)

        if self.transform_effect:
            self.draw_transform_effect(screen, self.transform_effect)

        torch_points = [
            (wx, wy, self.point((wx, wy)))
            for wx, wy in self.torches
            if -60 < wx - self.camera.x < VIEW.w + 60 and -60 < wy - self.camera.y < VIEW.h + 60
        ]
        self.draw_lighting(screen, torch_points, px, py, level.ghost)
        self.draw_torches(screen, torch_points)
        for wx, _, (px2, py2) in torch_points:
            self.draw_smoke(screen, wx, px2, py2)
        self.draw_dust(screen)

        screen.set_clip(None)
        self.draw_top_bar(screen)
        self.draw_sidebar(screen)
        if self.map_open:
            self.draw_map(screen)
        if level.won:
            self.draw_win(screen)
        elif level.lost:
            self.draw_loss(screen)

    def draw_souls(self, screen):
        for soul in self.souls:
            sx, sy = self.point(soul.position)
            frame = self.soul_sprite
            if soul.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (sx - 4, sy - 10))

    def draw_special_tiles(self, screen, level):
        for x, y, tile in self.special_tiles:
            px, py = self.point((x * 16 + 8, y * 16 + 8))
            if tile == "Y":
                rect = pygame.Rect(px - 8, py - 8, 16, 16)
                pygame.draw.rect(screen, (64, 62, 63), rect.inflate(-1, -1))
                pygame.draw.rect(screen, (129, 108, 58), rect.inflate(-4, -2), 1)
                for dx in (-4, 4):
                    pygame.draw.line(screen, (245, 209, 110), (px + dx, py - 5), (px + dx, py + 5))
                if level.ghost:
                    pygame.draw.line(screen, (155, 239, 226), (px - 2, py - 3), (px + 2, py + 3))
            elif tile == "E":
                pygame.draw.rect(screen, (29, 55, 49), (px - 10, py - 14, 20, 25))
                pygame.draw.rect(screen, (119, 232, 155), (px - 10, py - 14, 20, 25), 2, border_radius=8)
            elif tile == "K":
                if (x, y) in level.collected_key_positions:
                    continue
                bob = round(math.sin(self.elapsed * 3 + x * 1.7 + y * 2.3) * 2)
                screen.blit(self.key_glow, (px - 14, py - 14 + bob), special_flags=pygame.BLEND_RGBA_ADD)
                frame = self.tiles.art["key"]
                screen.blit(frame, (px - frame.get_width() // 2, py - frame.get_height() // 2 + bob))
            elif tile == "D":
                locked = level.keys_collected < level.keys_total
                rect = pygame.Rect(px - 8, py - 8, 16, 16)
                if locked:
                    pygame.draw.rect(screen, (74, 48, 34), rect.inflate(-1, -1))
                    pygame.draw.rect(screen, (40, 26, 18), rect.inflate(-1, -1), 2)
                    pygame.draw.line(screen, (40, 26, 18), (rect.centerx, rect.y + 2), (rect.centerx, rect.bottom - 2), 2)
                    pygame.draw.circle(screen, (214, 178, 90), (rect.centerx, rect.centery), 2)
                else:
                    pygame.draw.rect(screen, (30, 46, 36), rect.inflate(-4, -1))
                    pygame.draw.rect(screen, (140, 196, 150), rect.inflate(-4, -1), 1)

    def draw_player(self, screen, level, px, py):
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

    def draw_lighting(self, screen, torch_points, px, py, is_ghost):
        self.shade.fill((4, 7, 15, 210))
        radius = VISION_GHOST if is_ghost else VISION_ALIVE
        self.shade.blit(self.glow(radius, 235), (px - radius, py - VIEW.y - radius), special_flags=pygame.BLEND_RGBA_SUB)
        for _, _, (tx, ty) in torch_points:
            self.shade.blit(self.glow(43, 120), (tx - 43, ty - VIEW.y - 43), special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(self.shade, VIEW.topleft)

    def draw_torches(self, screen, torch_points):
        for wx, wy, (px2, py2) in torch_points:
            base_color, tip_color = flame_colors(wx, wy)
            pygame.draw.rect(screen, (93, 60, 39), (px2 - 2, py2, 4, 6))
            flame = 4 + int(math.sin(self.elapsed * 11 + wx) * 1.5)
            pygame.draw.polygon(screen, base_color, [(px2 - 3, py2), (px2, py2 - flame - 3), (px2 + 3, py2)])
            pygame.draw.line(screen, tip_color, (px2, py2), (px2, py2 - flame))

    def draw_smoke(self, screen, seed, px, py):
        """Fumee qui monte au-dessus d'une torche, entierement procedurale (fonction
        du temps ecoule), pas de particules a stocker/mettre a jour."""
        cycle = 1.8
        for i in range(2):
            t = (self.elapsed + seed * 0.017 + i * cycle / 2) % cycle
            frac = t / cycle
            sx = px + math.sin(t * 2.3 + seed) * 2
            sy = py - 6 - frac * 16
            alpha = int(55 * (1 - frac))
            radius = 1 + round(frac)
            if alpha > 4:
                pygame.draw.circle(screen, (*SMOKE_COLOR, alpha), (round(sx), round(sy)), radius)

    def draw_dust(self, screen):
        """Poussiere qui flotte dans l'air : discrete dans les salles ouvertes, plus
        grosse et plus dense dans les couloirs etroits (brume plus epaisse). Se
        disperse (repoussee + s'estompe) quand le joueur passe au travers."""
        player_pos = self.level.position
        for x0, y0, phase, speed, radius, alpha_mult in self.dust_motes:
            if not (-20 < x0 - self.camera.x < VIEW.w + 20 and -20 < y0 - self.camera.y < VIEW.h + 20):
                continue
            wx = x0 + math.sin(self.elapsed * 0.3 * speed + phase) * 10
            wy = y0 + math.cos(self.elapsed * 0.2 * speed + phase) * 6

            fade = 1.0
            dx, dy = wx - player_pos.x, wy - player_pos.y
            dist = math.hypot(dx, dy)
            if dist < DUST_DISPERSE_RADIUS:
                push = (DUST_DISPERSE_RADIUS - dist) / DUST_DISPERSE_RADIUS
                if dist > 0.01:
                    wx += dx / dist * push * DUST_DISPERSE_STRENGTH
                    wy += dy / dist * push * DUST_DISPERSE_STRENGTH
                fade = 1.0 - push * 0.85

            x, y = self.point((wx, wy))
            glow = 45 + int(25 * math.sin(self.elapsed * speed + phase))
            alpha = min(255, int(max(12, glow) * alpha_mult * fade))
            if alpha > 3:
                pygame.draw.circle(screen, (*DUST_COLOR, alpha), (x, y), radius)

    def draw_transform_effect(self, screen, effect):
        p = effect.progress
        x, y = self.point(effect.position)
        color = (150, 195, 235) if effect.expanding else (235, 225, 195)
        radius = 3 + round(26 * (p if effect.expanding else (1 - p)))
        alpha = round(220 * (1 - p))
        if radius > 1 and alpha > 0:
            pygame.draw.circle(screen, (*color, alpha), (x, y), radius, 2)
        for i in range(6):
            angle = math.radians(i * 60 + p * 90)
            dist = radius * 0.7
            dx, dy = math.cos(angle) * dist, math.sin(angle) * dist - p * 12
            pygame.draw.circle(screen, (*color, alpha), (round(x + dx), round(y + dy)), 2)

    def draw_top_bar(self, screen):
        pygame.draw.rect(screen, INK, (0, 0, PLAY_W, TOP_BAR_H))
        screen.blit(self.title_surface, (8, 2))
        screen.blit(self.zone_labels[self.current_room()], (8, 19))
        pygame.draw.line(screen, (61, 65, 64), (0, TOP_BAR_H - 1), (PLAY_W, TOP_BAR_H - 1))

    def draw_sidebar(self, screen):
        level = self.level
        pygame.draw.rect(screen, INK, SIDEBAR)
        pygame.draw.line(screen, (61, 65, 64), (SIDEBAR.x, 0), (SIDEBAR.x, SIDEBAR.h))

        x = SIDEBAR.x + 8
        y = 26
        screen.blit(self.inventory_title, (x, y))
        y += 18

        status = "AME ERRANTE" if level.ghost else "VIVANT"
        self.label(screen, status, (x, y), (154, 222, 211) if level.ghost else WHITE, self.small)
        y += 16
        self.label(screen, f"Poison : {level.mode.poison_potions.count}", (x, y), (192, 150, 228), self.small)
        y += 14
        self.label(screen, f"Resurrection : {level.mode.resurrection_potions.count}", (x, y), (150, 200, 228), self.small)
        y += 16

        if level.ghost:
            pygame.draw.rect(screen, (43, 48, 63), (x, y, SIDEBAR_W - 16, 4))
            pygame.draw.rect(screen, (172, 136, 223), (x, y, int((SIDEBAR_W - 16) * level.mode.time_remaining / level.mode.duration), 4))
            y += 12

        y += 8
        self.label(screen, "Objets :", (x, y), GOLD, self.small)
        y += 14
        self.label(screen, f"Cles : {level.keys_collected}/{level.keys_total}", (x, y), (235, 196, 90), self.small)

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
        self.label(screen, "N : recommencer    Echap : quitter", (SIZE[0] // 2 - 90, SIZE[1] // 2 + 10), WHITE, self.small)

    def draw_loss(self, screen):
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((30, 8, 12, 220))
        screen.blit(veil, (0, 0))
        self.label(screen, "VOUS ETES MORT", (SIZE[0] // 2 - 48, SIZE[1] // 2 - 10), (232, 120, 120), self.font)
        self.label(screen, "N : recommencer    Echap : quitter", (SIZE[0] // 2 - 90, SIZE[1] // 2 + 10), WHITE, self.small)


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

        # Plein ecran reel : on remplit tout l'ecran, sans bandes noires, sans
        # lissage (le rendu doit rester net, pas flou).
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
