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

MAP_PATH = Path(__file__).resolve().parents[1] / "assets/maps/training_corridor.json"


class TrainingLevel:
    def __init__(self, path=MAP_PATH):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.grid = self.data["grid"]
        self.width, self.height = len(self.grid[0]), len(self.grid)
        if not all(len(row) == self.width for row in self.grid):
            raise ValueError("Le plan doit etre rectangulaire")
        self.tile_size = self.data["tile_size"]
        self.spawn = self.data["spawn"]
        self.position = self.center(self.spawn)
        self.mode = GhostModeController(self.data["ghost_duration"])
        self.won = False
        self.message = "P : devenez fantome pour traverser. P a nouveau pour redevenir humain."
        self.message_time = 6.0

    @property
    def ghost(self):
        return self.mode.state is PlayerState.GHOST

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
        if self.won:
            return
        if key != pygame.K_p:
            return
        if not self.ghost:
            if self.mode.enter_ghost_mode(self.position):
                self.say("Votre corps reste ici. Traversez le mur dore.")
            else:
                self.say("Plus de fioles. R pour recommencer.")
        elif self.mode.potions.drink():
            self.mode.return_to_alive()
            self.say("Vous reprenez forme humaine, ici meme.")
        else:
            self.say("Plus de fioles pour redevenir humain : attendez que le temps s'ecoule.")

    def update(self, dt, direction=(0, 0)):
        if self.won:
            return
        dt = max(0, dt)
        self.message_time = max(0, self.message_time - dt)
        restored = self.mode.update(dt)
        if restored is not None:
            self.position.update(restored)
            self.say("Le temps est ecoule. Vous reprenez vie dans votre corps.")

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

        if not self.ghost and self.tile(*self.cell) == "E":
            self.won = True
            self.say("Sortie atteinte : le couloir est valide.")
        elif self.ghost and self.tile(*self.cell) == "E":
            self.say("Une ame ne peut pas franchir le seuil : redevenez humain (P).")
