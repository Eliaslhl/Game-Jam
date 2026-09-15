import pygame
from systems.interactions import InteractiveObject

class Door(InteractiveObject):
    def __init__(self, obj_id: str, x: int = 0, y: int = 0, closed_img: str = "assets/images/decor/door_closed.png", open_img: str = "assets/images/decor/door_open.png", **kwargs):
        super().__init__(obj_id=obj_id, image_path=closed_img, x=x, y=y, **kwargs)
        self.closed_image = self.image
        self.open_image = pygame.image.load(open_img).convert_alpha()
        self.is_open = False

    def toggle(self):
        self.is_open = not self.is_open
        self.image = self.open_image if self.is_open else self.closed_image