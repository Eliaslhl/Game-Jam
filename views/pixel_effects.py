"""Petits utilitaires de rendu partages entre les vues Pygame du projet
(couloir d'entrainement, sanctuaire) : sprites ASCII, halos lumineux et
signal de danger en fin de temps fantome.
"""
import math

import pygame

DANGER_THRESHOLD = 0.35
DANGER_COLOR = (214, 48, 48)

_vignette_holes = {}


def build_sprite(rows, palette):
    """Construit une petite Surface a partir de lignes de caracteres et d'une
    palette {caractere: couleur RGBA}. Sert pour les silhouettes type GAUNTLET."""
    image = pygame.Surface((max(map(len, rows)), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            image.set_at((x, y), palette[char])
    return image


def make_glow(radius, color, strength, exponent=0.7):
    """Cercle degrade transparent -> `color` au centre, utilise aussi bien pour
    les lueurs colorees (fontaine, symbole secret) que pour l'eclairage
    soustractif (assombrir tout sauf autour du joueur/des torches)."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(strength * (1 - r / radius) ** exponent)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


def lerp_color(a, b, t):
    """Interpole lineairement entre deux couleurs RGB, t fige a [0, 1]."""
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ghost_danger_intensity(time_remaining, duration, threshold=DANGER_THRESHOLD):
    """0 tant qu'il reste largement le temps de revenir a la vie ; monte
    progressivement vers 1 a mesure que la resurrection devient urgente."""
    if duration <= 0:
        return 0.0
    ratio = max(0.0, time_remaining / duration)
    if ratio > threshold:
        return 0.0
    return 1 - ratio / threshold


def danger_shake(elapsed, intensity, amplitude=4):
    """Petites secousses de camera/rendu, de plus en plus fortes a mesure que
    le temps presse (deux frequences desaccordees pour un mouvement organique,
    pas un simple aller-retour)."""
    if intensity <= 0:
        return 0.0, 0.0
    strength = amplitude * intensity
    return math.sin(elapsed * 47) * strength, math.cos(elapsed * 61) * strength * 0.7


def draw_danger_vignette(surface, rect, elapsed, intensity, color=DANGER_COLOR):
    """Halo rouge pulsant concentre sur les bords de `rect` (le centre reste
    lisible) : signale qu'il faut revenir vivant de toute urgence sans pour
    autant aveugler le joueur."""
    if intensity <= 0:
        return
    pulse = 0.7 + 0.3 * math.sin(elapsed * (5 + 9 * intensity))
    alpha = int(150 * intensity * pulse)
    if alpha <= 0:
        return
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    layer.fill((*color, alpha))
    hole_radius = max(rect.w, rect.h) * 2 // 3
    hole = _vignette_holes.get(hole_radius)
    if hole is None:
        hole = make_glow(hole_radius, (0, 0, 0), 255, exponent=0.8)
        _vignette_holes[hole_radius] = hole
    layer.blit(hole, (rect.w // 2 - hole_radius, rect.h // 2 - hole_radius), special_flags=pygame.BLEND_RGBA_SUB)
    surface.blit(layer, rect.topleft)
