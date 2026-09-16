"""Moteur du Sanctuaire des Veilleurs : camera, HUD et rendu (classe `SimpleMapGame`,
reprise par `views/puzzle_view.py` pour la partie jouable avec les enigmes).
Le decor statique (fontaines, salles thematiques) vit dans `map_theme.py`, les
effets dynamiques (ames errantes, transformation) dans `effects.py`, et les
petits utilitaires de rendu partages avec le couloir d'entrainement dans
`pixel_effects.py`.
"""
import math
import os
from pathlib import Path
import sys

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
    BLOOD_COLOR,
    DUST_COLOR,
    DUST_DISPERSE_RADIUS,
    DUST_DISPERSE_STRENGTH,
    SMOKE_COLOR,
    TransformEffect,
    build_corpse_sprite,
    build_soul_sprite,
    generate_dust_motes,
    make_souls,
)
from settings import (
    TITLE_FONT_FILE,
    UI_FONT_FILE,
    TEXT_DIM,
    DIVIDER,
    GHOST_STATUS,
    GHOST_BAR_BG,
    GHOST_BAR_FILL,
    POTION_COUNT,
    BACKGROUND_MUSIC,
    BACKGROUND_MUSIC_VOLUME
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
HOLE_VOID = (18, 10, 28)
HOLE_RIM = (172, 136, 223)
GAME_OVER_RED = (196, 30, 30)
PANEL_BG = (18, 24, 34)
RESURRECTION_COUNT = (150, 200, 228)
STATUS_ALIVE_BG = (30, 40, 33)
STATUS_GHOST_BG = (28, 42, 46)

VISION_ALIVE = 62
VISION_GHOST = 62


class SimpleMapGame:
    def __init__(self, scale=(1.0, 1.0), level=None):
        # Le decor (tuiles, sprites) reste en pixel-art brut, agrandi au nearest
        # neighbor par l'appelant : net et volontairement blocky. Le texte, lui,
        # est rendu directement a la resolution finale de la fenetre (voir
        # draw_text()) pour rester lisse, sans le flou d'un texte anticrenele
        # agrandi apres coup ni le cote "pixelise" d'un texte sans anticrenelage.
        self.scale_x, self.scale_y = scale
        self.level = TrainingLevel(MAP_PATH)
        self.level = level if level is not None else TrainingLevel(MAP_PATH)
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

        # Meme police que le menu principal (MedievalSharp) pour les titres, une
        # variante plus lisible en petite taille pour le corps du HUD. Tailles
        # calculees a la resolution finale (voir scale_x/scale_y ci-dessus).
        self.font = pygame.font.Font(str(TITLE_FONT_FILE), max(1, round(13 * self.scale_y)))
        self.small = pygame.font.Font(str(UI_FONT_FILE), max(1, round(11 * self.scale_y)))
        self.tiny = pygame.font.Font(str(UI_FONT_FILE), max(1, round(9 * self.scale_y)))
        self.yurei = YureiWalk()
        self.ghost_frames = [pygame.transform.scale(f, (13, 23)) for f in self.yurei.frames]
        self.soul_sprite = build_soul_sprite()
        self.corpse_sprite = build_corpse_sprite()
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
        self.danger_intensity = 0.0
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

        # Rendus une seule fois, a la bonne taille finale : anticrenelage actif
        # (True) puisqu'il n'y a plus de redimensionnement apres coup sur ce texte.
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
        """Rendu direct sur `screen` (deja a la resolution finale) : position
        donnee dans le repere du petit canevas pixel-art, mise a l'echelle ici."""
        surface = (font or self.font).render(text, True, color)
        screen.blit(surface, (position[0] * self.scale_x, position[1] * self.scale_y))

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

        mode = self.level.mode
        self.danger_intensity = (
            ghost_danger_intensity(mode.time_remaining, mode.duration) if self.level.ghost else 0.0
        )
        if self.danger_intensity:
            dx, dy = danger_shake(self.elapsed, self.danger_intensity)
            self.camera.x += dx
            self.camera.y += dy

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
            self.__init__(scale=(self.scale_x, self.scale_y))
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
        if level.ghost:
            self.draw_holes(screen, level)

        corpse = self.corpse_sprite
        for corpse_position in level.mode.corpse_positions:
            cx, cy = self.point(corpse_position)
            screen.blit(corpse, (cx - corpse.get_width() // 2, cy - corpse.get_height() // 2 + 4))

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
        if self.danger_intensity:
            draw_danger_vignette(screen, VIEW, self.elapsed, self.danger_intensity)

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

    def draw_holes(self, screen, level):
        for hx, hy in level.holes:
            px, py = self.point(level.center((hx, hy)))
            pygame.draw.circle(screen, HOLE_VOID, (px, py), 7)
            pygame.draw.circle(screen, HOLE_RIM, (px, py), 7, 1)

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
        if effect.expanding:
            for ox, oy, vx, vy, size in effect.blood:
                bx = round(x + ox + vx * p)
                by = round(y + oy + vy * p + 22 * p * p)
                blood_alpha = max(0, round(230 * (1 - p)))
                pygame.draw.circle(screen, (*BLOOD_COLOR, blood_alpha), (bx, by), max(1, round(size)))

    def draw_top_bar(self, screen):
        """Fond + separateur uniquement : les textes sont dans draw_top_bar_text()."""
        pygame.draw.rect(screen, INK, (0, 0, PLAY_W, TOP_BAR_H))
        pygame.draw.line(screen, DIVIDER, (0, TOP_BAR_H - 1), (PLAY_W, TOP_BAR_H - 1))

    def draw_top_bar_text(self, screen):
        screen.blit(self.title_surface, (8 * self.scale_x, 3 * self.scale_y))
        screen.blit(self.zone_labels[self.current_room()], (8 * self.scale_x, 19 * self.scale_y))

    def draw_sidebar(self, screen):
        """Fond, cadre et pictogrammes uniquement : les textes sont dans
        draw_sidebar_text(). Les deux methodes partagent la meme disposition,
        calculee une fois dans _sidebar_layout() pour rester synchronisees."""
        level = self.level
        pos = self._sidebar_layout()
        pygame.draw.rect(screen, PANEL_BG, SIDEBAR)
        pygame.draw.line(screen, GOLD, (SIDEBAR.x, 0), (SIDEBAR.x, SIDEBAR.h), 1)

        pygame.draw.line(screen, DIVIDER, (pos["x"], pos["div1_y"]), (pos["x"] + pos["w"], pos["div1_y"]))

        badge_bg = STATUS_GHOST_BG if level.ghost else STATUS_ALIVE_BG
        badge_fg = GHOST_STATUS if level.ghost else WHITE
        pygame.draw.rect(screen, badge_bg, pos["badge"], border_radius=4)
        pygame.draw.rect(screen, badge_fg, pos["badge"], width=1, border_radius=4)

        self._draw_potion_icon(screen, pos["x"], pos["poison_y"], POTION_COUNT)
        self._draw_potion_icon(screen, pos["x"], pos["resurrection_y"], RESURRECTION_COUNT)

        if pos["ghost_bar"] is not None:
            bar = pygame.Rect(*pos["ghost_bar"])
            pygame.draw.rect(screen, GHOST_BAR_BG, bar, border_radius=2)
            fill_w = max(0, int(bar.w * level.mode.time_remaining / level.mode.duration))
            if fill_w > 0:
                pygame.draw.rect(screen, GHOST_BAR_FILL, (bar.x, bar.y, fill_w, bar.h), border_radius=2)

        pygame.draw.line(screen, DIVIDER, (pos["x"], pos["div2_y"]), (pos["x"] + pos["w"], pos["div2_y"]))
        self._draw_key_pips(screen, pos["x"], pos["keys_y"], level.keys_collected, level.keys_total)

    def draw_sidebar_text(self, screen):
        level = self.level
        pos = self._sidebar_layout()
        x, w = pos["x"], pos["w"]

        screen.blit(self.inventory_title, (x * self.scale_x, pos["title_y"] * self.scale_y))

        status = "AME ERRANTE" if level.ghost else "VIVANT"
        badge_fg = GHOST_STATUS if level.ghost else WHITE
        bx, by, bw, bh = pos["badge"]
        status_surface = self.small.render(status, True, badge_fg)
        rect = status_surface.get_rect(
            center=((bx + bw / 2) * self.scale_x, (by + bh / 2) * self.scale_y)
        )
        screen.blit(status_surface, rect)

        self.label(screen, "FIOLES", (x, pos["fioles_label_y"]), TEXT_DIM, self.tiny)
        self._draw_potion_label(screen, x, w, pos["poison_y"], POTION_COUNT, "Poison", level.mode.poison_potions.count)
        self._draw_potion_label(
            screen, x, w, pos["resurrection_y"], RESURRECTION_COUNT, "Resurrection", level.mode.resurrection_potions.count
        )

        if pos["ghost_timer_y"] is not None:
            self.label(screen, f"Retour dans {level.mode.time_remaining:.1f}s", (x, pos["ghost_timer_y"]), GHOST_STATUS, self.tiny)

        self.label(screen, "OBJETS", (x, pos["objets_label_y"]), TEXT_DIM, self.tiny)
        self._draw_key_pips_text(screen, x, pos["keys_y"], level.keys_collected, level.keys_total)

    def _sidebar_layout(self):
        """Positions (repere petit canevas) partagees par les formes et le texte
        de la barre laterale, pour que les deux restent parfaitement alignes."""
        level = self.level
        x = SIDEBAR.x + 10
        w = SIDEBAR_W - 20
        y = 12
        pos = {"x": x, "w": w, "title_y": y}
        y += 14
        pos["div1_y"] = y
        y += 8
        badge_h = 16
        pos["badge"] = (x, y, w, badge_h)
        y += badge_h + 10
        pos["fioles_label_y"] = y
        y += 12
        pos["poison_y"] = y
        y += 13
        pos["resurrection_y"] = y
        y += 13
        y += 4
        if level.ghost:
            pos["ghost_timer_y"] = y
            y += 12
            pos["ghost_bar"] = (x, y, w, 5)
            y += 13
        else:
            pos["ghost_timer_y"] = None
            pos["ghost_bar"] = None
        y += 4
        pos["div2_y"] = y
        y += 8
        pos["objets_label_y"] = y
        y += 12
        pos["keys_y"] = y
        return pos

    def _draw_potion_icon(self, screen, x, y, color):
        """La fiole (petit rectangle colore) seule ; le nom et le compte sont
        dans _draw_potion_label()."""
        pygame.draw.rect(screen, color, (x, y + 1, 8, 10), border_radius=2)
        pygame.draw.rect(screen, INK, (x + 2, y, 4, 3))

    def _draw_potion_label(self, screen, x, w, y, color, label, count):
        self.label(screen, label, (x + 14, y), WHITE, self.tiny)
        count_surface = self.tiny.render(str(count), True, color)
        screen.blit(count_surface, ((x + w) * self.scale_x - count_surface.get_width(), y * self.scale_y))

    def _key_pips_fit(self, total):
        pip, gap = 10, 4
        return total > 0 and total * (pip + gap) - gap <= SIDEBAR_W - 20

    def _draw_key_pips(self, screen, x, y, collected, total):
        """Une rangee de petits carres (une cle = un pion) : d'un coup d'oeil,
        combien il en reste a trouver. Repli en texte si trop nombreuses (voir
        _draw_key_pips_text pour le texte associe)."""
        if not self._key_pips_fit(total):
            return
        pip, gap = 10, 4
        for i in range(total):
            px = x + i * (pip + gap)
            rect = pygame.Rect(px, y, pip, pip)
            if i < collected:
                pygame.draw.rect(screen, (235, 196, 90), rect, border_radius=2)
            else:
                pygame.draw.rect(screen, TEXT_DIM, rect, width=1, border_radius=2)

    def _draw_key_pips_text(self, screen, x, y, collected, total):
        if total <= 0:
            self.label(screen, "Aucune cle sur cette carte", (x, y), TEXT_DIM, self.tiny)
        elif self._key_pips_fit(total):
            self.label(screen, f"{collected}/{total}", (x, y + 14), (235, 196, 90), self.tiny)
        else:
            self.label(screen, f"Cles : {collected}/{total}", (x, y), (235, 196, 90), self.small)

    def draw_map(self, screen):
        """Fond + carte miniature uniquement : le texte est dans draw_map_text()."""
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

    def draw_map_text(self, screen):
        box = pygame.Rect(15, 15, SIZE[0] - 30, SIZE[1] - 30)
        self.label(screen, "CARTE (M pour fermer)", (box.x + 10, box.y + 6), GOLD, self.small)

    def draw_win(self, screen):
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((6, 16, 22, 220))
        screen.blit(veil, (0, 0))

    def draw_win_text(self, screen):
        self.label(screen, "SORTIE ATTEINTE", (SIZE[0] // 2 - 55, SIZE[1] // 2 - 10), GOLD, self.font)
        self.label(screen, "N : recommencer    Echap : quitter", (SIZE[0] // 2 - 90, SIZE[1] // 2 + 10), WHITE, self.small)

    def draw_loss(self, screen):
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((30, 8, 12, 220))
        screen.blit(veil, (0, 0))

    def draw_loss_text(self, screen):
        self.label(screen, "VOUS ETES MORT", (SIZE[0] // 2 - 48, SIZE[1] // 2 - 10), (232, 120, 120), self.font)
        self.label(screen, "N : recommencer    Echap : quitter", (SIZE[0] // 2 - 90, SIZE[1] // 2 + 10), WHITE, self.small)

    def draw_text(self, screen):
        """Deuxieme passe : tout le texte du HUD, dessine directement a la
        resolution finale de `screen` (net, ni flou ni pixelise), par-dessus le
        petit canevas pixel-art deja agrandi et blitte dessus par l'appelant."""
        level = self.level
        self.draw_top_bar_text(screen)
        self.draw_sidebar_text(screen)
        if self.map_open:
            self.draw_map_text(screen)
        if level.won:
            self.draw_win_text(screen)
        elif level.lost:
            self.draw_loss_text(screen)


def run(screen):
    """Boucle du sanctuaire dans une fenetre DEJA ouverte (ex : reprise de la
    fenetre du menu, meme taille). N'appelle ni pygame.init() ni pygame.quit() :
    c'est a l'appelant de gerer le cycle de vie de pygame."""
    target_size = screen.get_size()
    canvas = pygame.Surface(SIZE)
    scale = (target_size[0] / SIZE[0], target_size[1] / SIZE[1])
    game = SimpleMapGame(scale=scale)
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
        screen.blit(pygame.transform.scale(canvas, target_size), (0, 0))
        game.draw_text(screen)
        pygame.display.flip()
        if "--smoke-test" in sys.argv:
            running = False


def main():
    """Lancement autonome (python views/simple_map_view.py) : plein ecran reel,
    sans bandes noires, sans lissage (le rendu doit rester net, pas flou)."""
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
        except (pygame.error, OSError):
            # Le jeu reste jouable si le système audio n'est pas disponible.
            pass

        desktop = pygame.display.Info()
        desktop_size = (desktop.current_w or 1280, desktop.current_h or 720)
        window = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
        pygame.display.set_caption("Le sanctuaire - Deadweight")

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
                int(keys[pygame.K_d] or keys[pygame.K_RIGHT])
                - int(keys[pygame.K_q] or keys[pygame.K_a] or keys[pygame.K_LEFT]),
                int(keys[pygame.K_s] or keys[pygame.K_DOWN])
                - int(keys[pygame.K_z] or keys[pygame.K_w] or keys[pygame.K_UP]),
            )
            game.update(dt, direction)
            game.draw(canvas)
            window.blit(pygame.transform.scale(canvas, window.get_size()), (0, 0))
            pygame.display.flip()
            if "--smoke-test" in sys.argv:
                running = False
    finally:
        if music_started:
            pygame.mixer.music.stop()
        pygame.quit()


if __name__ == "__main__":
    main()
