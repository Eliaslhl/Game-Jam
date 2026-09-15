"""Identite visuelle du Sanctuaire des Veilleurs : rectangles des salles, themes,
decor statique (fontaines, bassin, tombes...) et teinte fantome. Tout est propre
a la geometrie de `assets/maps/sanctuaire_radial.json` (hub au centre, salle Nord
tout en haut, salle Sud-Est en bas a droite).
"""
import math
import random

import pygame

from views.pixel_effects import make_glow

HUB_CENTER = (25 * 16 + 8, 25 * 16 + 8)
NORTH_CENTER = (25 * 16 + 8, 8 * 16 + 8)
WATER_RECT = pygame.Rect(35 * 16, 35 * 16, 4 * 16, 4 * 16)

# Rectangles des 9 salles (memes constantes que le generateur de la carte), pour
# donner une identite propre a chaque zone : theme, teinte, decor, torches.
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

# Teinte "glace bleue" du monde en mode fantome (retenue parmi plusieurs essais).
GHOST_TINT_MULT = (150, 190, 230)
GHOST_TINT_ADD = (60, 70, 85)


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


def ghostly(surface):
    """Applique la teinte glace bleue du mode fantome a une surface (tuiles ou decor)."""
    tinted = pygame.transform.grayscale(surface)
    tinted.fill((*GHOST_TINT_MULT, 255), special_flags=pygame.BLEND_RGBA_MULT)
    tinted.fill((*GHOST_TINT_ADD, 0), special_flags=pygame.BLEND_RGB_ADD)
    return tinted


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


def draw_tombstone(surface, cx, cy):
    pygame.draw.rect(surface, (72, 76, 86, 255), (cx - 4, cy - 6, 8, 10), border_radius=2)
    pygame.draw.line(surface, (40, 44, 54, 255), (cx - 2, cy - 2), (cx + 2, cy - 2))
    pygame.draw.line(surface, (40, 44, 54, 255), (cx, cy - 4), (cx, cy))


def draw_cobweb(surface, x, y, flip_x=False, flip_y=False):
    sx, sy = (-1 if flip_x else 1), (-1 if flip_y else 1)
    for i in (4, 8, 12):
        pygame.draw.line(surface, (150, 150, 142, 90), (x + i * sx, y), (x, y + i * sy), 1)


def draw_secret_symbol(surface, cx, cy, color):
    """Symbole spectral invisible pour un vivant, revele seulement en fantome."""
    glow = make_glow(22, color, 190)
    surface.blit(glow, (cx - 22, cy - 22), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surface, (*color, 220), (cx, cy), 8, 1)
    pygame.draw.line(surface, (*color, 220), (cx - 6, cy - 6), (cx + 6, cy + 6), 1)
    pygame.draw.line(surface, (*color, 220), (cx - 6, cy + 6), (cx + 6, cy - 6), 1)


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


def build_room_decor(decor_surface, tiles, level):
    """Peint tout le decor statique (fontaines, bassin, identite de chaque salle)
    sur `decor_surface`. Appele une seule fois a la construction du niveau."""
    draw_fountain(decor_surface, *HUB_CENTER)
    draw_fountain(decor_surface, *NORTH_CENTER)
    draw_water(decor_surface, WATER_RECT)
    draw_statue(decor_surface, WATER_RECT.centerx, WATER_RECT.centery)
    draw_bush(decor_surface, WATER_RECT.x - 6, WATER_RECT.centery + 10)
    draw_bush(decor_surface, WATER_RECT.right + 6, WATER_RECT.centery - 10)
    scatter_leaves(decor_surface, level)

    wash_room(decor_surface, ROOM_RECTS["E"], level, (110, 85, 35), 55)
    scatter_art_in_room(decor_surface, tiles.art, "book", level, ROOM_RECTS["E"], 0.18, 11)

    wash_room(decor_surface, ROOM_RECTS["W"], level, (35, 55, 78), 60)
    scatter_art_in_room(decor_surface, tiles.art, "bones", level, ROOM_RECTS["W"], 0.12, 22)
    draw_tombstone(decor_surface, ROOM_RECTS["W"].x + 20, ROOM_RECTS["W"].y + 24)
    draw_tombstone(decor_surface, ROOM_RECTS["W"].right - 20, ROOM_RECTS["W"].bottom - 20)

    wash_room(decor_surface, ROOM_RECTS["NE"], level, (55, 65, 48), 50)
    draw_cobweb(decor_surface, ROOM_RECTS["NE"].x + 3, ROOM_RECTS["NE"].y + 3)
    draw_cobweb(decor_surface, ROOM_RECTS["NE"].right - 3, ROOM_RECTS["NE"].y + 3, flip_x=True)

    wash_room(decor_surface, ROOM_RECTS["NW"], level, (70, 48, 95), 55)

    wash_room(decor_surface, ROOM_RECTS["SW"], level, (90, 70, 40), 45)
    scatter_art_in_room(decor_surface, tiles.art, "plant", level, ROOM_RECTS["SW"], 0.15, 33)


def build_ghost_secrets(map_size):
    """Symboles spectraux, invisibles pour un vivant : le monde n'est pas le meme
    selon la forme du joueur."""
    surface = pygame.Surface(map_size, pygame.SRCALPHA)
    draw_secret_symbol(surface, *ROOM_RECTS["NW"].center, (190, 150, 235))
    draw_secret_symbol(surface, *ROOM_RECTS["W"].center, (150, 195, 235))
    return surface
