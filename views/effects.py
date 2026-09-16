"""Effets visuels dynamiques du Sanctuaire : ames errantes qui patrouillent,
animation de transformation vivant/fantome, et generation de la poussiere
ambiante. Le dessin de la poussiere/fumee reste dans la vue (il a besoin de la
camera courante), mais tout ce qui peut se calculer une fois vit ici.
"""
import random

import pygame

from views.pixel_effects import build_sprite

TRANSFORM_DURATION = 0.5

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


def build_soul_sprite():
    return build_sprite(GHOST_ROWS, SOUL_PALETTE)


def make_souls():
    return [WanderingSoul(path, speed=22 + i * 4) for i, path in enumerate(SOUL_PATROLS)]


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
    """Patrouille en boucle entre des points fixes, independamment du joueur."""

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


def generate_dust_motes(level, room_at, room_counts=(35, 55), radii=(1, 2), alpha_mults=(1.0, 1.6), seed=7):
    """Repartit la poussiere ambiante sur les cases de sol : moins nombreuse et
    plus fine dans les salles ouvertes, plus dense et plus grosse dans les
    couloirs etroits (brume plus epaisse). Chaque mote est un tuple
    (x0, y0, phase, vitesse, rayon, multiplicateur d'alpha) ; le mouvement est
    ensuite entierement procedural (fonction du temps ecoule), rien d'autre a
    mettre a jour a chaque frame.
    """
    rng = random.Random(seed)
    room_tiles, corridor_tiles = [], []
    for y in range(level.height):
        for x in range(level.width):
            if level.tile(x, y) != ".":
                continue
            (room_tiles if room_at(x * 16 + 8, y * 16 + 8) else corridor_tiles).append((x, y))

    def make_motes(tiles, count, radius, alpha_mult):
        motes = []
        for _ in range(count):
            tx, ty = rng.choice(tiles)
            x0 = tx * 16 + rng.uniform(2, 14)
            y0 = ty * 16 + rng.uniform(2, 14)
            motes.append((x0, y0, rng.uniform(0, 6.28), rng.uniform(0.6, 1.4), radius, alpha_mult))
        return motes

    return make_motes(room_tiles, room_counts[0], radii[0], alpha_mults[0]) + make_motes(
        corridor_tiles, room_counts[1], radii[1], alpha_mults[1]
    )
