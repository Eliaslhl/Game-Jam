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

from entities.ghost import YureiWalk
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

# Rectangles des 9 salles (memes constantes que le generateur de sanctuaire_radial.json),
# pour donner une identite propre a chaque zone : theme, teinte, decor, torches.
ROOM_RECTS = {
    "hub": pygame.Rect(352, 352, 112, 112),
    "N": pygame.Rect(352, 80, 112, 96),
    "S": pygame.Rect(352, 624, 112, 96),
    "E": pygame.Rect(624, 352, 112, 96),
    "W": pygame.Rect(80, 352, 112, 96),
    "NE": pygame.Rect(544, 160, 96, 96),
    "NW": pygame.Rect(160, 160, 96, 96),
    "SE": pygame.Rect(544, 544, 96, 96),
    "SW": pygame.Rect(160, 544, 96, 96),
}
ROOM_THEMES = {
    "hub": "Le Sanctuaire",
    "N": "L'Autel",
    "S": "L'Entree",
    "E": "La Bibliotheque",
    "W": "Les Cryptes",
    "NE": "La Salle Abandonnee",
    "NW": "La Salle Fantome",
    "SE": "Le Jardin",
    "SW": "La Chapelle",
}
COLD_TORCH_ROOMS = {"W", "NW"}

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

# Poussiere/fumee ambiantes : gris, plus grosses/denses dans les couloirs.
DUST_COLOR = (200, 205, 215)
SMOKE_COLOR = (175, 175, 180)
DUST_DISPERSE_RADIUS = 26
DUST_DISPERSE_STRENGTH = 14

GHOST_ROWS = ["..www..", ".wwwww.", ".wWwWw.", ".wwwww.", ".wwwww.", "w.w.w.w"]

# Ames errantes : silhouette ASCII simple (le joueur, lui, utilise le vrai sprite
# Yurei de Kadir), teinte violette pour les distinguer. Visibles uniquement en
# mode fantome, elles patrouillent en permanence dans leur salle.
SOUL_PALETTE = {".": (0, 0, 0, 0), "w": (176, 150, 210), "W": (140, 116, 178)}
SOUL_PATROLS = [
    [(175, 200), (233, 200)],   # Salle Fantome
    [(208, 175), (208, 233)],   # Salle Fantome (croise la premiere)
    [(100, 400), (172, 400)],   # Cryptes
    [(136, 368), (136, 432)],   # Cryptes (croise la troisieme)
    [(552, 175), (610, 208), (552, 233)],  # Salle Abandonnee
]


TRANSFORM_DURATION = 0.5


class TransformEffect:
    """Anneau + particules au moment ou le joueur change de forme (vivant <-> fantome)."""

    def __init__(self, position, expanding):
        self.position = pygame.Vector2(position)
        self.expanding = expanding
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def done(self):
        return self.elapsed >= TRANSFORM_DURATION

    @property
    def progress(self):
        return min(1.0, self.elapsed / TRANSFORM_DURATION)


class WanderingSoul:
    def __init__(self, waypoints, speed=26):
        self.waypoints = waypoints
        self.position = pygame.Vector2(waypoints[0])
        self.target_index = 1 % len(waypoints)
        self.speed = speed
        self.facing_left = False

    def update(self, dt):
        target = pygame.Vector2(self.waypoints[self.target_index])
        to_target = target - self.position
        distance = to_target.length()
        if distance < 2:
            self.target_index = (self.target_index + 1) % len(self.waypoints)
            return
        step = to_target.normalize() * min(self.speed * dt, distance)
        self.facing_left = step.x < 0
        self.position += step


def build_sprite(rows, palette):
    image = pygame.Surface((max(map(len, rows)), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            image.set_at((x, y), palette[char])
    return image


GHOST_TINT_MULT = (150, 190, 230)
GHOST_TINT_ADD = (60, 70, 85)


def ghostly(surface):
    """Teinte 'glace bleue' du monde en mode fantome (retenue parmi les essais)."""
    tinted = pygame.transform.grayscale(surface)
    tinted.fill((*GHOST_TINT_MULT, 255), special_flags=pygame.BLEND_RGBA_MULT)
    tinted.fill((*GHOST_TINT_ADD, 0), special_flags=pygame.BLEND_RGB_ADD)
    return tinted


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


def wash_room(surface, rect, level, color, alpha):
    """Teinte legere du sol d'une salle, pour lui donner une ambiance propre."""
    tile = 16
    for ty in range(rect.y // tile, (rect.y + rect.h) // tile):
        for tx in range(rect.x // tile, (rect.x + rect.w) // tile):
            if level.tile(tx, ty) == ".":
                pygame.draw.rect(surface, (*color, alpha), (tx * tile, ty * tile, tile, tile))


def scatter_art_in_room(surface, art, name, level, rect, rate, seed):
    """Repartit un sprite ASCII existant (livre, ossements, plante...) dans une salle."""
    tile = 16
    for ty in range(rect.y // tile, (rect.y + rect.h) // tile):
        for tx in range(rect.x // tile, (rect.x + rect.w) // tile):
            if level.tile(tx, ty) != ".":
                continue
            rng = random.Random((tx * 92821) ^ (ty * 68917) ^ seed)
            if rng.random() < rate:
                surface.blit(art[name], (tx * tile + 3, ty * tile + 3))


def draw_tombstone(surface, cx, cy):
    pygame.draw.rect(surface, (72, 76, 86, 255), (cx - 4, cy - 6, 8, 10), border_radius=2)
    pygame.draw.line(surface, (40, 44, 54, 255), (cx - 2, cy - 2), (cx + 2, cy - 2))
    pygame.draw.line(surface, (40, 44, 54, 255), (cx, cy - 4), (cx, cy))


def draw_cobweb(surface, x, y, flip_x=False, flip_y=False):
    sx, sy = (-1 if flip_x else 1), (-1 if flip_y else 1)
    for i in (4, 8, 12):
        pygame.draw.line(surface, (150, 150, 142, 90), (x + i * sx, y), (x, y + i * sy), 1)
    pygame.draw.line(surface, (150, 150, 142, 70), (x + 8 * sx, y), (x, y + 8 * sy), 1)


def draw_secret_symbol(surface, cx, cy, color):
    """Symbole spectral invisible pour un vivant, revele seulement en fantome."""
    glow = make_glow(22, color, 190)
    surface.blit(glow, (cx - 22, cy - 22), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surface, (*color, 220), (cx, cy), 8, 1)
    pygame.draw.line(surface, (*color, 220), (cx - 6, cy - 6), (cx + 6, cy + 6), 1)
    pygame.draw.line(surface, (*color, 220), (cx - 6, cy + 6), (cx + 6, cy - 6), 1)


def room_at(x, y):
    for name, rect in ROOM_RECTS.items():
        if rect.collidepoint(x, y):
            return name
    return None


def flame_colors(x, y):
    """Flamme spectrale bleu-blanc dans les Cryptes / la Salle Fantome, orange ailleurs."""
    if room_at(x, y) in COLD_TORCH_ROOMS:
        return (90, 150, 205), (190, 225, 245)
    return (205, 112, 47), (255, 223, 131)


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
        self.tiles_ghost_surface = ghostly(self.tiles.surface)

        map_size = (self.level.width * 16, self.level.height * 16)
        self.decor_surface = pygame.Surface(map_size, pygame.SRCALPHA)
        draw_fountain(self.decor_surface, *HUB_CENTER)
        draw_fountain(self.decor_surface, *NORTH_CENTER)
        draw_water(self.decor_surface, WATER_RECT)
        draw_statue(self.decor_surface, WATER_RECT.centerx, WATER_RECT.centery)
        draw_bush(self.decor_surface, WATER_RECT.x - 6, WATER_RECT.centery + 10)
        draw_bush(self.decor_surface, WATER_RECT.right + 6, WATER_RECT.centery - 10)
        scatter_leaves(self.decor_surface, self.level)

        # Identite de chaque salle : teinte + decor propre, pour que chacune "raconte
        # quelque chose" au lieu d'etre une piece anonyme.
        wash_room(self.decor_surface, ROOM_RECTS["E"], self.level, (110, 85, 35), 55)
        scatter_art_in_room(self.decor_surface, self.tiles.art, "book", self.level, ROOM_RECTS["E"], 0.18, 11)

        wash_room(self.decor_surface, ROOM_RECTS["W"], self.level, (35, 55, 78), 60)
        scatter_art_in_room(self.decor_surface, self.tiles.art, "bones", self.level, ROOM_RECTS["W"], 0.12, 22)
        draw_tombstone(self.decor_surface, ROOM_RECTS["W"].x + 20, ROOM_RECTS["W"].y + 24)
        draw_tombstone(self.decor_surface, ROOM_RECTS["W"].right - 20, ROOM_RECTS["W"].bottom - 20)

        wash_room(self.decor_surface, ROOM_RECTS["NE"], self.level, (55, 65, 48), 50)
        draw_cobweb(self.decor_surface, ROOM_RECTS["NE"].x + 3, ROOM_RECTS["NE"].y + 3)
        draw_cobweb(self.decor_surface, ROOM_RECTS["NE"].right - 3, ROOM_RECTS["NE"].y + 3, flip_x=True)

        wash_room(self.decor_surface, ROOM_RECTS["NW"], self.level, (70, 48, 95), 55)

        wash_room(self.decor_surface, ROOM_RECTS["SW"], self.level, (90, 70, 40), 45)
        scatter_art_in_room(self.decor_surface, self.tiles.art, "plant", self.level, ROOM_RECTS["SW"], 0.15, 33)

        self.decor_ghost_surface = ghostly(self.decor_surface)

        # Secrets visibles uniquement en fantome : le monde n'est pas le meme selon
        # la forme du joueur.
        self.ghost_secrets_surface = pygame.Surface(map_size, pygame.SRCALPHA)
        draw_secret_symbol(self.ghost_secrets_surface, *ROOM_RECTS["NW"].center, (190, 150, 235))
        draw_secret_symbol(self.ghost_secrets_surface, *ROOM_RECTS["W"].center, (150, 195, 235))

        self.tiles_with_decor = self.tiles.surface.copy()
        self.tiles_with_decor.blit(self.decor_surface, (0, 0))

        # Brouillard de guerre pour la carte (M) : seules les cases visitees sont
        # reconstituees ; le reste reste noir tant qu'on n'y est pas passe.
        self.explored = set()
        self.revealed_surface = pygame.Surface((self.level.width * 16, self.level.height * 16))

        # Poussiere ambiante : positions et phases fixes, le mouvement est
        # entierement procedural (fonction de self.elapsed), pas d'etat a mettre a jour.
        # Plus grosse et plus dense dans les couloirs (etroits, propices a une brume
        # epaisse) que dans les salles ouvertes (juste quelques particules discretes).
        dust_rng = random.Random(7)
        room_tiles, corridor_tiles = [], []
        for y in range(self.level.height):
            for x in range(self.level.width):
                if self.level.tile(x, y) != ".":
                    continue
                (room_tiles if room_at(x * 16 + 8, y * 16 + 8) else corridor_tiles).append((x, y))

        def make_motes(tiles, count, radius, alpha_mult):
            motes = []
            for _ in range(count):
                tx, ty = dust_rng.choice(tiles)
                x0 = tx * 16 + dust_rng.uniform(2, 14)
                y0 = ty * 16 + dust_rng.uniform(2, 14)
                motes.append((x0, y0, dust_rng.uniform(0, 6.28), dust_rng.uniform(0.6, 1.4), radius, alpha_mult))
            return motes

        self.dust_motes = make_motes(room_tiles, 35, 1, 1.0) + make_motes(corridor_tiles, 55, 2, 1.6)

        self.font = pygame.font.Font(None, 18)
        self.small = pygame.font.Font(None, 14)
        self.yurei = YureiWalk()
        self.ghost_frames = [pygame.transform.scale(f, (13, 23)) for f in self.yurei.frames]
        self.soul_sprite = build_sprite(GHOST_ROWS, SOUL_PALETTE)
        self.souls = [WanderingSoul(path, speed=22 + i * 4) for i, path in enumerate(SOUL_PATROLS)]
        self.transform_effect = None
        self.was_ghost = False

        self.map_w = self.level.width * 16
        self.map_h = self.level.height * 16
        # La salle est plus grande que l'ecran de jeu : camera qui suit le joueur,
        # avec sa petite zone eclairee autour de lui. La carte entiere reste
        # consultable via M (draw_map), en net (pas de flou).
        self.camera = pygame.Vector2()
        self.update_camera()
        self.reveal_around(self.level.position)

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

    def reveal_around(self, position, radius_tiles=6):
        cx, cy = int(position.x // 16), int(position.y // 16)
        for y in range(max(0, cy - radius_tiles), min(self.level.height, cy + radius_tiles + 1)):
            for x in range(max(0, cx - radius_tiles), min(self.level.width, cx + radius_tiles + 1)):
                if (x, y) in self.explored or (x - cx) ** 2 + (y - cy) ** 2 > radius_tiles ** 2:
                    continue
                self.explored.add((x, y))
                self.revealed_surface.blit(self.tiles_with_decor, (x * 16, y * 16), (x * 16, y * 16, 16, 16))

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
        self.reveal_around(self.level.position)
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
        if level.ghost:
            screen.blit(self.ghost_secrets_surface, (-self.camera.x, VIEW.y - self.camera.y))
            for soul in self.souls:
                sx, sy = self.point(soul.position)
                frame = self.soul_sprite
                if soul.facing_left:
                    frame = pygame.transform.flip(frame, True, False)
                screen.blit(frame, (sx - 4, sy - 10))

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
            index = int(self.elapsed / 0.14) % len(self.ghost_frames) if self.moving else 0
            frame = self.ghost_frames[index]
            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (px - 6, py - 19))
        else:
            frame = self.tiles.art["player"]
            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (px - 5, py - 8 - (int(self.elapsed * 8) % 2 if self.moving else 0)))

        if self.transform_effect:
            self.draw_transform_effect(screen, self.transform_effect)

        torch_points = [
            (wx, wy, self.point((wx, wy)))
            for wx, wy in self.torches
            if -60 < wx - self.camera.x < VIEW.w + 60 and -60 < wy - self.camera.y < VIEW.h + 60
        ]

        self.shade.fill((4, 7, 15, 210))
        radius = VISION_GHOST if level.ghost else VISION_ALIVE
        self.shade.blit(self.glow(radius, 235), (px - radius, py - VIEW.y - radius), special_flags=pygame.BLEND_RGBA_SUB)
        for wx, wy, (tx, ty) in torch_points:
            self.shade.blit(self.glow(43, 120), (tx - 43, ty - VIEW.y - 43), special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(self.shade, VIEW.topleft)

        for wx, wy, (px2, py2) in torch_points:
            base_color, tip_color = flame_colors(wx, wy)
            pygame.draw.rect(screen, (93, 60, 39), (px2 - 2, py2, 4, 6))
            flame = 4 + int(math.sin(self.elapsed * 11 + wx) * 1.5)
            pygame.draw.polygon(screen, base_color, [(px2 - 3, py2), (px2, py2 - flame - 3), (px2 + 3, py2)])
            pygame.draw.line(screen, tip_color, (px2, py2), (px2, py2 - flame))

        for wx, wy, (px2, py2) in torch_points:
            self.draw_smoke(screen, wx, px2, py2)
        self.draw_dust(screen)

        screen.set_clip(None)
        self.draw_top_bar(screen)
        self.draw_sidebar(screen)
        if self.map_open:
            self.draw_map(screen)
        if level.won:
            self.draw_win(screen)

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
        """Poussiere doree qui flotte dans l'air : discrete dans les salles ouvertes,
        plus grosse et plus dense dans les couloirs etroits (brume plus epaisse).
        Se disperse (repoussee + s'estompe) quand le joueur passe au travers."""
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
        self.label(screen, "-", (x, y), (139, 156, 163), self.small)

    def draw_map(self, screen):
        box = pygame.Rect(15, 15, SIZE[0] - 30, SIZE[1] - 30)
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((6, 10, 16, 210))
        screen.blit(veil, (0, 0))
        pygame.draw.rect(screen, (18, 25, 34), box)
        pygame.draw.rect(screen, (100, 96, 77), box, 1)

        scale = min((box.w - 10) / self.map_w, (box.h - 10) / self.map_h)
        scaled = pygame.transform.scale(self.revealed_surface, (round(self.map_w * scale), round(self.map_h * scale)))
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
