import pygame
from systems.interactions import InteractiveObject

class SpectralLever(InteractiveObject):
    def __init__(self, obj_id: str, x: int = 0, y: int = 0, off_img: str = "assets/images/decor/lever_off.png", on_img: str = "assets/images/decor/lever_on.png", **kwargs):
        super().__init__(obj_id=obj_id, image_path=off_img, x=x, y=y, **kwargs)
        self.off_image = self.image
        self.on_image = pygame.image.load(on_img).convert_alpha()

    def interact(self, player_sprite, all_objects: list) -> bool:
        if not self.can_interact(player_sprite):
            return False

        self.is_active = not self.is_active
        self.image = self.on_image if self.is_active else self.off_image

        for obj in all_objects:
            if getattr(obj, "obj_id", None) == self.target_id and hasattr(obj, "toggle"):
                obj.toggle()
        return True