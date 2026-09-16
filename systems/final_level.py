"""Niveau final de Kadir : donnees ASCII et regles, independantes du rendu."""
import json
import math
from pathlib import Path
import pygame
from systems.ghost_mode import GhostModeController, PlayerState
from systems.interactions import can_interact
from systems.hazards import GhostHazards

MAP_PATH = Path(__file__).resolve().parents[1] / 'assets/maps/labyrinthe_des_ames_kadir.json'

HOLE_COUNT = 6


class FinalLevel:
    def __init__(self, path=MAP_PATH):
        self.data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.grid = self.data['grid']
        self.width, self.height = len(self.grid[0]), len(self.grid)
        if not all(len(row) == self.width for row in self.grid):
            raise ValueError('Le plan doit etre rectangulaire')
        self.tile_size = self.data['tile_size']
        self.position = self.center(self.data['spawn'])
        self.mode = GhostModeController(self.data['ghost_duration'], auto_return_on_timeout=True)
        self.seals, self.doors, self.keys, self.picked = set(), set(), set(), set()
        self.explored = set()
        self.discoveries = set()
        self.won = False
        self.dead = False
        self.holes = GhostHazards(self._floor_cells(), count=HOLE_COUNT)
        self.time = 0.0
        self.deaths = 0
        self.hurt_cooldown = 0.0
        self.message = 'Les murs dores cachent des secrets. P pour devenir fantome.'
        self.message_time = 8.0
        self.reveal()

    def _floor_cells(self):
        """Cases de sol nu ('.') eligibles pour un trou, hors case de spawn."""
        spawn_cell = tuple(self.data['spawn'])
        return [cell for cell in self.cells('.') if cell != spawn_cell]

    @property
    def ghost(self):
        return self.mode.state is PlayerState.GHOST

    @property
    def vision(self):
        return 142 if self.ghost else 94

    def center(self, cell):
        return pygame.Vector2((cell[0] + .5) * self.tile_size, (cell[1] + .5) * self.tile_size)

    @property
    def cell(self):
        return int(self.position.x // self.tile_size), int(self.position.y // self.tile_size)

    def tile(self, x, y):
        return self.grid[y][x] if 0 <= x < self.width and 0 <= y < self.height else '#'

    def cells(self, symbols):
        return [(x, y) for y, row in enumerate(self.grid) for x, t in enumerate(row) if t in symbols]

    def passable(self, x, y, ghost=None):
        ghost = self.ghost if ghost is None else ghost
        tile = self.tile(x, y)
        if tile == '#':
            return False
        if tile in 'Y~c':
            return ghost
        if tile in 'ABC':
            return tile in self.doors
        return True

    def blocked(self, position):
        # La collision porte sur les pieds, pas sur les cheveux du sprite.
        x, y = position
        return any(not self.passable(int(px // self.tile_size), int(py // self.tile_size))
                   for px in (x-4, x+4) for py in (y-4, y+4))

    def say(self, message):
        self.message, self.message_time = message, 6.0

    def action(self, key):
        if self.won or self.dead:
            return
        if key == pygame.K_p:
            if self.mode.enter_ghost_mode(self.position):
                self.say('Votre corps reste ici. Suivez les murs dores et les lueurs violettes.')
            elif self.ghost:
                self.say('Vous etes deja une ame. Entree pour revenir au corps.')
            else:
                self.say('Plus de fioles. Cherchez une potion violette ou R pour recommencer.')
        elif key == pygame.K_RETURN and self.ghost:
            self.position.update(self.mode.return_to_alive())
            self.say('De retour au corps. Les sceaux decouverts restent en memoire.')
        elif key == pygame.K_e:
            if not can_interact(self.mode.state):
                self.say('Une ame ne peut pas actionner les mecanismes physiques.')
                return
            nearby = sorted(self.cells('ABCO'), key=lambda c: self.center(c).distance_to(self.position))
            for cell in nearby:
                if self.center(cell).distance_to(self.position) > 28:
                    break
                tile = self.tile(*cell)
                if tile in 'ABC':
                    if tile.lower() in self.seals:
                        self.doors.add(tile)
                        self.say('Le sceau repond. La chambre est ouverte.')
                    else:
                        self.say('Porte scellee : cherchez son symbole en fantome dans cette aile.')
                    return
                lore = ['Les vivants possedent les cles. Les morts en connaissent le chemin.',
                        'Les fioles sont rares. Revenez au corps avec Entree des le secret trouve.',
                        'La brume repousse les vivants, mais eclaire les souvenirs des ames.',
                        'Trois ailes, trois souvenirs. Au sud-est, le seuil attend vos cles.']
                self.discoveries.add(cell)
                self.say(lore[self.cells('O').index(cell)])
                return

    def update(self, dt, direction=(0, 0)):
        if self.won or self.dead:
            return
        dt = max(0, dt)
        self.time += dt
        self.message_time = max(0, self.message_time - dt)
        self.hurt_cooldown = max(0, self.hurt_cooldown - dt)
        restored = self.mode.update(dt)
        if restored is not None:
            self.position.update(restored)
            self.say('Le temps est ecoule. Vous reprenez vie dans votre corps.')
        direction = pygame.Vector2(direction)
        if direction.length_squared():
            direction = direction.normalize()
        move = direction * (78 if self.ghost else 65) * dt
        for _ in range(max(1, math.ceil(move.length()/3))):
            step = move / max(1, math.ceil(move.length()/3))
            for axis in ('x', 'y'):
                candidate = self.position.copy()
                setattr(candidate, axis, getattr(candidate, axis) + getattr(step, axis))
                if not self.blocked(candidate):
                    self.position.update(candidate)
        if self.holes.is_lethal(self.cell):
            self.dead = True
            self.say('Un trou spectral vous a englouti.')
            return
        if self.ghost:
            for cell in self.cells('abc'):
                tile = self.tile(*cell)
                if self.center(cell).distance_to(self.position) < 23 and tile not in self.seals:
                    self.seals.add(tile)
                    self.say('Sceau ' + self.data['seals'][tile] + ' memorise. Revenez vivant ouvrir sa porte avec E.')
        tile = self.tile(*self.cell)
        if not self.ghost:
            if tile in '123' and tile not in self.keys:
                self.keys.add(tile)
                self.say(f'Cle {len(self.keys)}/3 retrouvee. Le seuil se trouve au sud-est.')
            if tile == 'P' and self.cell not in self.picked:
                self.picked.add(self.cell)
                self.mode.potions.count += 1
                self.say('Une fiole de poison retrouvee. Choisissez bien votre prochain passage.')
            if tile == '^' and self.hurt_cooldown <= 0:
                self.position.update(self.center(self.data['spawn']))
                self.deaths += 1
                self.hurt_cooldown = 1.0
                self.say('Les pics vous ramenent au sanctuaire. Vos decouvertes sont conservees.')
            if tile == 'E':
                if len(self.keys) == 3:
                    self.won = True
                    self.say('Les trois ames sont reunies. Le passage est ouvert.')
                else:
                    self.say(f'Le seuil attend encore {3-len(self.keys)} cle(s).')
        elif tile in '123':
            self.say('Cette cle appartient au monde physique. Revenez vivant.')
        self.reveal()

    def reveal(self):
        cx, cy = self.cell
        radius = math.ceil(self.vision/self.tile_size)
        for y in range(max(0, cy-radius), min(self.height, cy+radius+1)):
            for x in range(max(0, cx-radius), min(self.width, cx+radius+1)):
                if self.center((x,y)).distance_to(self.position) < self.vision:
                    self.explored.add((x,y))

    def zone(self):
        x,y = self.cell
        for zone in self.data['zones']:
            left,top,w,h = zone['rect']
            if left <= x < left+w and top <= y < top+h:
                return zone
        return {'name':'LES GALERIES', 'subtitle':'Chaque detour raconte une histoire', 'tint':[65,80,94]}
