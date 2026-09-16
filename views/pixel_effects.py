"""Petits utilitaires de rendu partages entre les vues Pygame du projet
(couloir d'entrainement, sanctuaire) : sprites ASCII et halos lumineux.
"""
import pygame


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
