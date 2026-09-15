"""Vue de travail : uniquement les murs et le sol de la map de Kadir."""
import os
import sys
from pathlib import Path
import pygame
from systems.final_level import FinalLevel
from views.pixel_art import PixelTiles

BASE_PATH = Path(__file__).resolve().parents[1] / 'assets/maps/base_vide_kadir.json'
WINDOW = (800, 560)
VIEW = pygame.Rect(0, 36, 800, 488)


class EmptyMapView:
    def __init__(self):
        self.level = FinalLevel(BASE_PATH)
        self.tiles = PixelTiles(self.level, decorate=False).surface
        self.font = pygame.font.Font(None, 24)
        self.small = pygame.font.Font(None, 20)
        self.fit_zoom = min(VIEW.w / self.tiles.get_width(), VIEW.h / self.tiles.get_height())
        self.center = pygame.Vector2(self.tiles.get_rect().center)
        self.zoom = self.fit_zoom
        self.scaled = None
        self.set_zoom(self.zoom)

    def set_zoom(self, zoom):
        self.zoom = max(self.fit_zoom, min(3, zoom))
        size = tuple(max(1, round(value * self.zoom)) for value in self.tiles.get_size())
        self.scaled = pygame.transform.scale(self.tiles, size)

    def reset(self):
        self.center.update(self.tiles.get_rect().center)
        self.set_zoom(self.fit_zoom)

    def update(self, dt, direction):
        self.center += pygame.Vector2(direction) * 300 * dt / self.zoom
        for axis, length, visible in [('x', self.tiles.get_width(), VIEW.w), ('y', self.tiles.get_height(), VIEW.h)]:
            margin = min(length / 2, visible / self.zoom / 2)
            setattr(self.center, axis, max(margin, min(length-margin, getattr(self.center, axis))))

    def draw(self, screen):
        screen.fill((12,17,25))
        screen.set_clip(VIEW)
        offset = pygame.Vector2(VIEW.center) - self.center * self.zoom
        screen.blit(self.scaled, (round(offset.x), round(offset.y)))
        screen.set_clip(None)
        screen.blit(self.font.render('BASE VIDE - KADIR', True, (225,213,185)), (16,9))
        screen.blit(self.small.render('M : toute la map   |   Molette / +/- : zoom   |   Fleches / ZQSD : deplacer   |   Echap : quitter', True, (202,209,215)), (16,538))


def main():
    if '--smoke-test' in sys.argv:
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    try:
        screen = pygame.display.set_mode(WINDOW)
        pygame.display.set_caption('Base vide de la map - Kadir')
        view = EmptyMapView()
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(clock.tick(60)/1000, .05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEWHEEL:
                    view.set_zoom(view.zoom * 1.2 ** event.y)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_m:
                        view.reset()
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        view.set_zoom(view.zoom * 1.2)
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        view.set_zoom(view.zoom / 1.2)
            keys = pygame.key.get_pressed()
            direction = (int(keys[pygame.K_RIGHT] or keys[pygame.K_d])-int(keys[pygame.K_LEFT] or keys[pygame.K_q] or keys[pygame.K_a]), int(keys[pygame.K_DOWN] or keys[pygame.K_s])-int(keys[pygame.K_UP] or keys[pygame.K_z] or keys[pygame.K_w]))
            view.update(dt, direction)
            view.draw(screen)
            pygame.display.flip()
            if '--smoke-test' in sys.argv:
                running = False
    finally:
        pygame.quit()
