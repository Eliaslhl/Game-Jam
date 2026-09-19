import math
import pygame

class InteractiveObject(pygame.sprite.Sprite):
    def __init__(self, obj_id: str, image_path: str, x: int = 0, y: int = 0, target_id: str = "", ghost_only: bool = False):
        super().__init__()
        self.obj_id = obj_id
        self.target_id = target_id
        self.ghost_only = ghost_only
        self.is_active = False

        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))

    def is_near(self, player_sprite, distance: float = 45.0) -> bool:
        """Calcule la distance euclidienne entre les centres des deux sprites."""
        dx = self.rect.centerx - player_sprite.rect.centerx
        dy = self.rect.centery - player_sprite.rect.centery
        return math.hypot(dx, dy) <= distance

    def can_interact(self, player_sprite) -> bool:
        if not self.is_near(player_sprite):
            return False
        if self.ghost_only and not getattr(player_sprite, "is_ghost", False):
            return False
        return True

    def interact(self, player_sprite, all_objects: list):
        pass