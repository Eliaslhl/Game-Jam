"""Map de test Pygame de Kadir, inspiree du plan ASCII de GAUNTLET."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from systems.ghost_mode import GhostModeController, PlayerState
from systems.interactions import can_interact, is_visible
from entities.ghost import YureiWalk

TILE = 40
RENDER_SIZE = (800, 935)
WINDOW_SIZE = (640, 748)
# B : mur normal ; Y : mur jaune ; I : indice fantome ; K : cle ; L : levier.
PLAN = (
    'BBBBBBBBBBBBBBBBBBBB',
    'B     B            B',
    'B     Y  I         B',
    'B     B            B',
    'B     B K          B',
    'B     Y            B',
    'B     B            B',
    'B     B            B',
    'B     Y            B',
    'B     B            B',
    'B     B            B',
    'B     Y            B',
    'B     B            B',
    'B     B            B',
    'B     Y            B',
    'B     B            B',
    'B  L  D         E  B',
    'B     B            B',
    'B     B            B',
    'BBBBBBBBBBBBBBBBBBBB',
)


class TestMapKadir:
    def __init__(self):
        self.mode = GhostModeController()
        self.position = pygame.Vector2(100, 100)
        self.animation = YureiWalk()
        self.facing_left = False
        self.key_collected = False
        self.door_open = False
        self.won = False
        self.message = 'P : boire une potion. Cherche un indice derriere le mur jaune.'
        self.font = pygame.font.Font(None, 23)
        self.small = pygame.font.Font(None, 20)

    @property
    def body(self):
        return pygame.Rect(round(self.position.x - 11), round(self.position.y - 11), 22, 22)

    def tiles(self):
        for y, row in enumerate(PLAN):
            for x, tile in enumerate(row):
                yield tile, pygame.Rect(x * TILE, y * TILE, TILE, TILE)

    def blocked(self, rect):
        if not pygame.Rect(0, 0, 800, 800).contains(rect):
            return True
        for tile, wall in self.tiles():
            solid = tile == 'B' or (tile == 'Y' and not self.mode.can_pass_wall(True)) or (tile == 'D' and not self.door_open)
            if solid and rect.colliderect(wall):
                return True
        return False

    def move(self, direction, dt):
        if direction.length_squared():
            direction = direction.normalize()
        # Petits pas pour ne jamais sauter une collision avec un grand delta.
        movement = direction * 180 * dt
        steps = max(1, int(movement.length() / 5) + 1)
        for _ in range(steps):
            for axis in ('x', 'y'):
                old = getattr(self.position, axis)
                setattr(self.position, axis, old + getattr(movement, axis) / steps)
                if self.blocked(self.body):
                    setattr(self.position, axis, old)
        if direction.x:
            self.facing_left = direction.x < 0

    def action(self, key):
        if key == pygame.K_p:
            if self.mode.enter_ghost_mode(self.position):
                self.message = 'Fantome : murs jaunes uniquement. Aucun objet physique utilisable.'
            else:
                self.message = 'Deja fantome ou plus de potions ! R pour recommencer.'
        elif key == pygame.K_e:
            for tile, rect in self.tiles():
                if tile == 'L' and self.position.distance_to(rect.center) < 60:
                    if can_interact(self.mode.state, tile):
                        self.door_open = True
                        self.message = 'Passage ouvert ! Recupere la cle puis rejoins la sortie verte.'
                    else:
                        self.message = 'Un fantome ne peut pas actionner le levier.'

    def update(self, dt, direction):
        restored = self.mode.update(dt)
        if restored is not None:
            self.position.update(restored)
            self.message = 'Retour au corps. Utilise les informations trouvees en fantome.'
        if self.won:
            return
        self.move(direction, dt)
        for tile, rect in self.tiles():
            if not self.body.colliderect(rect):
                continue
            if tile == 'I' and is_visible(self.mode.state, True):
                self.message = 'Indice : le levier est en bas a gauche. Vivant, appuie sur E.'
            elif tile == 'K' and not self.key_collected:
                if can_interact(self.mode.state, tile):
                    self.key_collected = True
                    self.message = 'Cle recuperee ! Rejoins la sortie verte.'
                else:
                    self.message = 'Impossible de ramasser une cle en fantome.'
            elif tile == 'E' and self.key_collected and can_interact(self.mode.state, tile):
                self.won = True
                self.message = 'Bravo ! Parcours termine. R pour recommencer.'

    def draw(self, screen, dt, moving):
        screen.fill((18, 22, 33))
        for tile, rect in self.tiles():
            pygame.draw.rect(screen, (29, 35, 46), rect, 1)
            if tile in 'BY' or (tile == 'D' and not self.door_open):
                pygame.draw.rect(screen, (56, 69, 95), rect.inflate(-2, -2), border_radius=3)
                if tile == 'Y':
                    pygame.draw.rect(screen, (255, 217, 68), rect.inflate(-24, -8), border_radius=5)
                if tile == 'D':
                    pygame.draw.rect(screen, (147, 95, 53), rect.inflate(-8, -2))
            elif tile == 'I' and is_visible(self.mode.state, True):
                screen.blit(self.font.render('?', True, (130, 245, 255)), rect.move(14, 8))
            elif tile == 'K' and not self.key_collected:
                pygame.draw.circle(screen, (255, 210, 50), rect.center, 8, 3)
                pygame.draw.line(screen, (255, 210, 50), rect.center, rect.move(12, 0).center, 3)
            elif tile == 'L':
                pygame.draw.rect(screen, (100, 185, 125), rect.inflate(-14, -14))
                screen.blit(self.small.render('E', True, 'white'), rect.move(15, 12))
            elif tile == 'E':
                pygame.draw.rect(screen, (40, 155, 110), rect.inflate(-4, -4), 3)
        if self.mode.state is PlayerState.GHOST:
            center = self.mode.corpse_position
            pygame.draw.ellipse(screen, (142, 104, 104), (center[0] - 15, center[1] - 7, 30, 14))
            self.animation.draw(screen, self.position, dt, moving, self.facing_left)
        else:
            pygame.draw.circle(screen, (104, 195, 255), self.body.center, 13)
            pygame.draw.circle(screen, 'white', (self.body.centerx + 4, self.body.centery - 4), 3)
        pygame.draw.rect(screen, (13, 16, 25), (0, 800, 800, 130))
        state = 'FANTOME' if self.mode.state is PlayerState.GHOST else 'VIVANT'
        lines = [f'KADIR | {state} | Potions : {self.mode.potions.count}/3 | Cle : {int(self.key_collected)}/1',
                 'Fleches / ZQSD / WASD : bouger | P : potion | E : levier | R : reset | Echap : quitter',
                 self.message]
        for i, line in enumerate(lines):
            screen.blit(self.small.render(line, True, (225, 232, 243)), (12, 811 + i * 25))
        pygame.draw.rect(screen, (50, 60, 75), (12, 892, 776, 12))
        pygame.draw.rect(screen, (133, 231, 241), (12, 892, int(776 * self.mode.time_remaining / self.mode.duration), 12))
        screen.blit(self.small.render(f'Temps fantome : {self.mode.time_remaining:.1f} s', True, 'white'), (12, 910))


def main():
    pygame.init()
    try:
        window = pygame.display.set_mode(WINDOW_SIZE)
        screen = pygame.Surface(RENDER_SIZE)
        pygame.display.set_caption('Map test Kadir - Mode fantome')
        game = TestMapKadir()
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(clock.tick(60) / 1000, 0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        game = TestMapKadir()
                    else:
                        game.action(event.key)
            keys = pygame.key.get_pressed()
            direction = pygame.Vector2(int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_q] or keys[pygame.K_a]), int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_z] or keys[pygame.K_w]))
            game.update(dt, direction)
            game.draw(screen, dt, bool(direction.length_squared()) and not game.won)
            pygame.transform.smoothscale(screen, WINDOW_SIZE, window)
            pygame.display.flip()
            if '--smoke-test' in sys.argv:
                running = False
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
