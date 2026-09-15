import pygame
import sys
from systems.levers import SpectralLever
from systems.doors_keys import Door

pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Test Puzzles Pygame")
clock = pygame.time.Clock()

# Joueur fictif
class DummyPlayer(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 50, 50)) # Rouge = Vivant
        self.rect = self.image.get_rect(center=(100, 200))
        self.is_ghost = False

    def toggle_ghost(self):
        self.is_ghost = not self.is_ghost
        self.image.fill((50, 200, 255) if self.is_ghost else (255, 50, 50))

player = DummyPlayer()
door = Door(obj_id="door_1", x=400, y=180)
lever = SpectralLever(obj_id="lever_1", target_id="door_1", ghost_only=True, x=250, y=180)

all_objects = [door, lever]
all_sprites = pygame.sprite.Group(door, lever, player)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.toggle_ghost()
            elif event.key == pygame.K_e:
                lever.interact(player, all_objects)

    # Déplacement simple
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: player.rect.x -= 4
    if keys[pygame.K_RIGHT]: player.rect.x += 4
    if keys[pygame.K_UP]: player.rect.y -= 4
    if keys[pygame.K_DOWN]: player.rect.y += 4

    screen.fill((30, 30, 40))
    all_sprites.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()