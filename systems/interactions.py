import math
import pygame
from systems.ghost_mode import PlayerState


def can_interact(player_state, target=None) -> bool:
    """Détermine si l'entité courante peut interagir selon son état."""
    return player_state is PlayerState.ALIVE


def is_visible(player_state, ghost_only: bool = False) -> bool:
    """Vérifie la visibilité d'un objet selon l'état du joueur."""
    return not ghost_only or player_state is PlayerState.GHOST


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

        # Récupération de l'état (compatible avec l'enum de Kadir ou un booléen is_ghost)
        player_state = getattr(player_sprite, "state", None)
        if player_state is None:
            player_state = PlayerState.GHOST if getattr(player_sprite, "is_ghost", False) else PlayerState.ALIVE

        # Un objet réservé au fantôme nécessite l'état GHOST, sinon l'état ALIVE
        if self.ghost_only:
            return player_state is PlayerState.GHOST
        return player_state is PlayerState.ALIVE

    def interact(self, player_sprite, all_objects: list):
        pass