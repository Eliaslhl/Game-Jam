# Responsable : Thaïs — boucle de jeu, affichage, entrées clavier

import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE,
    TILE_SIZE, MUR, MUR_FISSURE, PORTE,
    CLE, FIOLE, LEVIER, SORTIE, TEMPS_LIMITE_NIVEAU_1,
)
from systems.level_manager import charger_labyrinthe, PLAN_NIVEAU_1


class GameView:
    def __init__(self):
        self.maze_grid = None
        self.sprites_murs = None
        self.objets = None
        self.position = pygame.Vector2()
        self.grid_position = (0, 0)
        self.est_fantome = False
        self.nb_fioles = 3
        self.nb_cles = 0
        self.cadavres = []
        self.temps_restant = TEMPS_LIMITE_NIVEAU_1
        self.leviers_actives = set()
        self.running = True

    def setup(self):
        self.maze_grid, self.sprites_murs, self.objets = charger_labyrinthe(PLAN_NIVEAU_1)
        self.grid_position = (5, 1)
        self.position.update(self._center(self.grid_position))
        self.est_fantome = False
        self.nb_fioles = 3
        self.nb_cles = 0
        self.cadavres = []
        self.leviers_actives.clear()
        self.temps_restant = TEMPS_LIMITE_NIVEAU_1

    def ajouter_cadavre(self, x, y):
        self.cadavres.append(self._center((x, y)))

    @staticmethod
    def _center(cell):
        return (cell[0] * TILE_SIZE + TILE_SIZE // 2,
                cell[1] * TILE_SIZE + TILE_SIZE // 2)

    def _cell_rect(self, cell):
        return pygame.Rect(cell[0] * TILE_SIZE, cell[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def _passable(self, cell):
        tile = self.maze_grid.get(cell, MUR)
        if tile == MUR:
            return False
        if tile == MUR_FISSURE:
            return self.est_fantome
        if tile == PORTE:
            return self.nb_cles > 0 or bool(self.leviers_actives)
        return True

    def _move(self, dx, dy):
        target = (self.grid_position[0] + dx, self.grid_position[1] + dy)
        if self._passable(target):
            self.grid_position = target
            self.position.update(self._center(target))
            self.verifier_interactions()

    def on_draw(self):
        self.screen.fill((18, 22, 30))
        for cell, tile in self.maze_grid.items():
            rect = self._cell_rect(cell)
            if tile == MUR:
                pygame.draw.rect(self.screen, (55, 61, 72), rect)
            elif tile == MUR_FISSURE:
                pygame.draw.rect(self.screen, (170, 130, 45), rect)
                pygame.draw.rect(self.screen, (245, 205, 100), rect, 3)
            elif tile == PORTE:
                pygame.draw.rect(self.screen, (105, 66, 42), rect)
            elif tile != ".":
                pygame.draw.rect(self.screen, (30, 36, 45), rect)

        for x, y, tile in self.objets:
            center = self._center((x, y))
            color = {
                CLE: (240, 210, 65),
                FIOLE: (150, 90, 220),
                LEVIER: (220, 100, 65),
                SORTIE: (80, 210, 130),
                PORTE: (139, 94, 60),
            }[tile]
            pygame.draw.circle(self.screen, color, center, TILE_SIZE // 5)

        for corpse in self.cadavres:
            pygame.draw.ellipse(self.screen, (125, 115, 120), (corpse[0] - 18, corpse[1] - 9, 36, 18))
        player_color = (155, 225, 215) if self.est_fantome else (80, 150, 240)
        pygame.draw.circle(self.screen, player_color, self.position, TILE_SIZE // 4)

        font = pygame.font.Font(None, 28)
        hud = f"Fioles: {self.nb_fioles}   Cles: {self.nb_cles}   Temps: {max(0, int(self.temps_restant))}"
        self.screen.blit(font.render(hud, True, (235, 235, 235)), (12, 12))

    def on_update(self, delta_time):
        self.temps_restant -= delta_time
        if self.temps_restant <= 0:
            self.echec_niveau()

    def echec_niveau(self):
        # à décider avec l'équipe : écran de game over, relance du niveau, etc.
        print("Temps écoulé !")
        self.setup()

    def on_key_press(self, key, modifiers):
        directions = {
            pygame.K_UP: (0, 1), pygame.K_z: (0, 1),
            pygame.K_DOWN: (0, -1), pygame.K_s: (0, -1),
            pygame.K_LEFT: (-1, 0), pygame.K_q: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
        }
        if key in directions:
            self._move(*directions[key])
        elif key == pygame.K_SPACE:
            self.transformer()

        self.verifier_interactions()

    def transformer(self):
        if self.est_fantome or self.nb_fioles <= 0:
            return
        self.nb_fioles -= 1
        self.est_fantome = True
        self.ajouter_cadavre(*self.grid_position)

    def verifier_interactions(self):
        case = self.grid_position
        type_case = self.maze_grid.get(case)

        if self.est_fantome:
            return  # le fantôme ne peut rien ramasser ni activer

        if type_case == CLE:
            self.nb_cles += 1
            self.maze_grid[case] = "."

        elif type_case == FIOLE:
            self.nb_fioles += 1
            self.maze_grid[case] = "."

        elif type_case == LEVIER:
            self.leviers_actives.add(case)
            # à relier à une porte précise selon le design du niveau

        elif type_case == SORTIE and self.nb_cles > 0:
            print("Niveau terminé !")
            self.running = False


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(SCREEN_TITLE)
    game_view = GameView()
    game_view.screen = screen
    game_view.setup()
    clock = pygame.time.Clock()
    while game_view.running:
        delta_time = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_view.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_view.running = False
                else:
                    game_view.on_key_press(event.key, None)
        game_view.on_update(delta_time)
        game_view.on_draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
