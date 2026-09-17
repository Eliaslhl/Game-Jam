"""Niveau d'entrainement : couloir en ligne droite, meme moteur que le niveau final de Kadir.

Reprend la structure de `final_level.py` (plan ASCII, collisions, mode fantome) mais
sans cles/portes/sceaux : juste un mur normal, un segment de mur dore (traversable
en fantome) et une sortie, pour valider la mecanique vivant/fantome.
"""
import json
import math
from pathlib import Path

import pygame

from systems.ghost_mode import GhostModeController, PlayerState
from systems.hazards import GhostHazards

MAP_PATH = Path(__file__).resolve().parents[1] / "assets/maps/training_corridor.json"

HOLE_COUNT = 4


class TrainingLevel:
    def __init__(self, path=MAP_PATH, hole_count=None):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.grid = self.data["grid"]
        self.width, self.height = len(self.grid[0]), len(self.grid)
        if not all(len(row) == self.width for row in self.grid):
            raise ValueError("Le plan doit etre rectangulaire")
        self.tile_size = self.data["tile_size"]
        self.spawn = self.data["spawn"]
        self.position = self.center(self.spawn)
        self.mode = GhostModeController(self.data["ghost_duration"])
        self.keys_total = sum(row.count("K") for row in self.grid)
        self.keys_collected = 0
        self.collected_key_positions = set()
        self.won = False
        # hole_count=0 desactive les pieges (ex : le couloir d'entrainement, ou
        # on ne veut pas surprendre le joueur avant la vraie partie).
        self.holes = GhostHazards(self._floor_cells(), count=HOLE_COUNT if hole_count is None else hole_count)
        self.lost = False
        # Memes touches que la vraie partie : le tutoriel ne doit pas enseigner
        # des reflexes qui trahissent ensuite (voir action()).
        self.message = "P : devenez fantome pour traverser. P ou Entree pour revenir au corps."
        self.message_time = 6.0

    def _is_pinch_point(self, x, y):
        """Case situee dans un passage large d'une seule tuile (couloir etroit,
        pas de case parallele pour contourner) : un piege ici bloquerait
        totalement le passage plutot que d'etre simplement evitable."""
        def wall(cx, cy):
            return self.tile(cx, cy) == "#"
        pinched_horizontally = wall(x - 1, y) and wall(x + 1, y)
        pinched_vertically = wall(x, y - 1) and wall(x, y + 1)
        return pinched_horizontally or pinched_vertically

    def _floor_cells(self):
        """Cases de sol nu ('.') eligibles pour un trou, hors case de spawn et
        hors couloirs larges d'une seule case (voir _is_pinch_point)."""
        spawn_cell = tuple(self.spawn)
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.tile(x, y) == "."
            and (x, y) != spawn_cell
            and not self._is_pinch_point(x, y)
        ]

    @property
    def ghost(self):
        return self.mode.state is PlayerState.GHOST

    @property
    def dead(self):
        return self.mode.state is PlayerState.DEAD

    @property
    def vision(self):
        return 142 if self.ghost else 94

    def center(self, cell):
        return pygame.Vector2((cell[0] + 0.5) * self.tile_size, (cell[1] + 0.5) * self.tile_size)

    @property
    def cell(self):
        return int(self.position.x // self.tile_size), int(self.position.y // self.tile_size)

    def tile(self, x, y):
        return self.grid[y][x] if 0 <= x < self.width and 0 <= y < self.height else "#"

    def passable(self, x, y, ghost=None):
        ghost = self.ghost if ghost is None else ghost
        tile = self.tile(x, y)
        if tile == "#":
            return False
        if tile == "Y":
            return ghost
        if tile == "D":
            return self.keys_collected >= self.keys_total
        return True

    def blocked(self, position):
        x, y = position
        return any(
            not self.passable(int(px // self.tile_size), int(py // self.tile_size))
            for px in (x - 4, x + 4)
            for py in (y - 4, y + 4)
        )

    def say(self, message):
        self.message, self.message_time = message, 6.0

    def action(self, key):
        if self.won or self.lost:
            return
        # Exactement les memes touches que la partie (PuzzleLevel.action) : P ou
        # Entree fait l'aller-retour vivant/fantome. R n'est PAS la resurrection
        # ici, c'est le redemarrage comme en jeu - l'inverse s'apprenait dans le
        # tutoriel et faisait perdre sa partie au joueur d'un seul appui.
        if key in (pygame.K_p, pygame.K_RETURN) and self.ghost:
            if self.mode.return_to_alive(self.position) is not None:
                self.say("Vous ressuscitez a votre position actuelle.")
            else:
                self.say("Plus de fioles de resurrection.")
        elif key == pygame.K_p:
            if self.mode.enter_ghost_mode(self.position):
                self.say("Votre corps reste ici. Traversez le mur dore.")
            else:
                self.say("Plus de fioles de poison.")

    def update(self, dt, direction=(0, 0)):
        if self.won or self.lost:
            return
        dt = max(0, dt)
        self.message_time = max(0, self.message_time - dt)
        restored = self.mode.update(dt)
        if self.dead:
            self.lost = True
            self.say("Le temps est ecoule : vous etes mort. N pour recommencer.")
            return

        direction = pygame.Vector2(direction)
        if direction.length_squared():
            direction = direction.normalize()
        move = direction * (78 if self.ghost else 65) * dt
        steps = max(1, math.ceil(move.length() / 3))
        step = move / steps
        for _ in range(steps):
            for axis in ("x", "y"):
                candidate = self.position.copy()
                setattr(candidate, axis, getattr(candidate, axis) + getattr(step, axis))
                if not self.blocked(candidate):
                    self.position.update(candidate)

        if self.holes.is_lethal(self.cell):
            self.mode.die()
            self.lost = True
            self.say("Un trou spectral vous a englouti.")
            return

        cell = self.cell
        if self.tile(*cell) == "K" and cell not in self.collected_key_positions:
            self.collected_key_positions.add(cell)
            self.keys_collected += 1
            self.say(f"Cle trouvee ({self.keys_collected}/{self.keys_total}).")

        if not self.ghost and self.tile(*self.cell) == "E":
            self.won = True
            self.say("Sortie atteinte : le couloir est valide.")
        elif self.ghost and self.tile(*self.cell) == "E":
            self.say("Une ame ne peut pas franchir le seuil : redevenez humain (P).")
