# Responsable : à assigner — boucle de jeu, affichage, entrées clavier

import arcade
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE,
    CLE, FIOLE, LEVIER, SORTIE, TEMPS_LIMITE_NIVEAU_1,
)
from entities.player import Player
from systems.level_manager import charger_labyrinthe, PLAN_NIVEAU_1


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.maze_grid = None
        self.sprites_murs = None
        self.objets = None
        self.player = None
        self.cadavres = arcade.SpriteList()
        self.temps_restant = TEMPS_LIMITE_NIVEAU_1
        self.leviers_actives = set()  # cases (x, y) des leviers activés

    def setup(self):
        self.maze_grid, self.sprites_murs, self.objets = charger_labyrinthe(PLAN_NIVEAU_1)
        self.player = Player(grid_x=5, grid_y=1)  # à ajuster selon le point d'entrée du plan
        self.cadavres = arcade.SpriteList()
        self.temps_restant = TEMPS_LIMITE_NIVEAU_1

    def ajouter_cadavre(self, x, y):
        from corpse import Corpse
        self.cadavres.append(Corpse(x, y))

    def on_draw(self):
        self.clear()
        self.sprites_murs.draw()
        self.cadavres.draw()
        arcade.draw_sprite(self.player)

        arcade.draw_text(f"Fioles : {self.player.nb_fioles}", 10, SCREEN_HEIGHT - 20, arcade.color.WHITE, 14)
        arcade.draw_text(f"Clés : {self.player.nb_cles}", 10, SCREEN_HEIGHT - 40, arcade.color.WHITE, 14)
        arcade.draw_text(f"Temps : {int(self.temps_restant)}", 10, SCREEN_HEIGHT - 60, arcade.color.WHITE, 14)

    def on_update(self, delta_time):
        self.temps_restant -= delta_time
        if self.temps_restant <= 0:
            self.echec_niveau()

    def echec_niveau(self):
        # à décider avec l'équipe : écran de game over, relance du niveau, etc.
        print("Temps écoulé !")
        self.setup()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.player.deplacer(0, 1, self.maze_grid)
        elif key == arcade.key.DOWN:
            self.player.deplacer(0, -1, self.maze_grid)
        elif key == arcade.key.LEFT:
            self.player.deplacer(-1, 0, self.maze_grid)
        elif key == arcade.key.RIGHT:
            self.player.deplacer(1, 0, self.maze_grid)
        elif key == arcade.key.SPACE:
            self.player.transformer(self)

        self.verifier_interactions()

    def verifier_interactions(self):
        case = (self.player.grid_x, self.player.grid_y)
        type_case = self.maze_grid.get(case)

        if self.player.est_fantome:
            return  # le fantôme ne peut rien ramasser ni activer

        if type_case == CLE:
            self.player.ramasser_cle()
            self.maze_grid[case] = "."

        elif type_case == FIOLE:
            self.player.ramasser_fiole()
            self.maze_grid[case] = "."

        elif type_case == LEVIER:
            self.leviers_actives.add(case)
            # à relier à une porte précise selon le design du niveau

        elif type_case == SORTIE and self.player.nb_cles > 0:
            print("Niveau terminé !")
            # passer au niveau suivant (à implémenter)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_view = GameView()
    game_view.setup()
    window.show_view(game_view)
    arcade.run()


if __name__ == "__main__":
    main()
