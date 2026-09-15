"""Animation Pygame de Yurei Walk. Responsable : Kadir."""
from pathlib import Path
import pygame


class YureiWalk:
    def __init__(self):
        path = Path(__file__).resolve().parents[3] / 'assets/sprites/Yurei/Walk.png'
        sheet = pygame.image.load(str(path)).convert_alpha()
        size = sheet.get_height()
        self.frames = []
        for x in range(0, sheet.get_width(), size):
            frame = sheet.subsurface((x, 0, size, size))
            bounds = frame.get_bounding_rect()
            self.frames.append(pygame.transform.scale(frame.subsurface(bounds), (28, 48)))
        self.elapsed = 0.0

    def draw(self, screen, center, dt, moving, facing_left):
        self.elapsed = self.elapsed + dt if moving else 0.0
        frame = self.frames[int(self.elapsed / 0.14) % len(self.frames)]
        if facing_left:
            frame = pygame.transform.flip(frame, True, False)
        screen.blit(frame, frame.get_rect(midbottom=(center[0], center[1] + 14)))
