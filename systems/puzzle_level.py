"""Les trois enigmes du sanctuaire : observer mort, resoudre vivant."""
import math
import random
from itertools import product
from pathlib import Path
import pygame
from systems.training_level import TrainingLevel
from systems.puzzle_manager import PuzzleManager
from systems.hazards import GhostHazards
from entities.puzzle_object import PuzzleObject

MAP_PATH = Path(__file__).resolve().parents[1] / 'assets/maps/sanctuaire_enigmes.json'


class PuzzleLevel(TrainingLevel):
    _previous_path = None
    def __init__(self, path=MAP_PATH, seed=None):
        super().__init__(path)
        self.generate_path(seed)
        # Le chemin invisible n'existe qu'a partir d'ici (ajoute a self.data['objects']
        # par generate_path) : on relance les trous pour qu'aucun ne tombe dessus, sinon
        # l'enigme du chemin deviendrait injouable (un pas obligatoire serait mortel).
        self.holes = GhostHazards(self._floor_cells(), count=len(self.holes))
        self.puzzles = PuzzleManager(self.data['puzzles'], seed=seed)
        self.objects = [PuzzleObject.from_data(d) for d in self.data['objects']]
        # Les indices et la validation partagent exactement la meme permutation.
        for obj in self.objects:
            if obj.clue_target:
                rank = self.puzzles.puzzles[obj.puzzle_id].solution.index(obj.clue_target)
                member=obj.clue_target.rsplit('_',1)[-1]
                sequence=self.puzzles.puzzles[obj.puzzle_id].solution
                if rank==0:
                    obj.text=f'La statue {member} veille avant toutes les autres.'
                else:
                    previous=sequence[rank-1].rsplit('_',1)[-1]
                    obj.text=f'La statue {member} ne repond qu apres la statue {previous}.'
            elif obj.clue_index is not None:
                sequence=[m.rsplit('_',1)[-1] for m in self.puzzles.puzzles[obj.puzzle_id].solution]
                obj.text=[f'{sequence[0]} doit preceder {sequence[1]}.',
                          f'{sequence[2]} attend que {sequence[1]} ait parle.',
                          f'Le veilleur {sequence[0]} ouvre le rituel.'][obj.clue_index]
        self.time = 0.0
        self.key_ready_at = {}
        self.keys = set()
        self.keys_total = 3
        self.cooldown = 0.0
        self.events = []
        self.feedback = ''
        self.feedback_time = 0.0
        self.previous_path_cell = None
        self.mode.poison_potions.count = 3
        self.mode.resurrection_potions.count = 3
        self.say('Trois salles, trois cles. P : observer en fantome. E : interagir vivant.')

    def _floor_cells(self):
        """Comme TrainingLevel, mais sans les cases occupees par les objets des
        enigmes (statues, leviers, indices, cles, portes, coffres) : les trous
        spectraux restent dangereux ailleurs sur la carte, mais n'apparaissent
        jamais sur un element d'enigme qu'ils recouvriraient inutilement."""
        object_cells = {tuple(o['cell']) for o in self.data['objects']}
        return [cell for cell in super()._floor_cells() if cell not in object_cells]

    def generate_path(self, seed):
        """Chemin orthogonal sans boucle, de l'entree a la cle du jardin."""
        rng=random.Random(seed) if seed is not None else random.SystemRandom()
        candidates=[]
        for targets in product(range(35,40),repeat=3):
            cells=[(37,34)]
            x=37
            for y,target in zip(range(35,39),(*targets,39)):
                cells.append((x,y))
                while x!=target:
                    x+=1 if target>x else -1
                    cells.append((x,y))
            if len(cells)<=19 and (seed is not None or tuple(cells)!=self._previous_path):
                candidates.append(cells)
        cells=rng.choice(candidates)
        if seed is None:type(self)._previous_path=tuple(cells)
        self.objects_path=cells
        definitions=self.data['objects']
        self.data['objects']=[o for o in definitions if o['type']!='footprint']
        for i,cell in enumerate(cells):
            self.data['objects'].append(dict(id=f'step_{i}',type='footprint',cell=cell,
                puzzle_id='path_green',visible_state='ghost',interaction_allowed=False,text=''))
        puzzle=next(p for p in self.data['puzzles'] if p['id']=='path_green')
        puzzle['solution']=[f'step_{i}' for i in range(len(cells))]
        puzzle['required_clues']=list(puzzle['solution'])

    def passable(self, x, y, ghost=None):
        ghost = self.ghost if ghost is None else ghost
        tile = self.tile(x,y)
        if tile == '#': return False
        if tile == 'Y': return ghost
        for obj in getattr(self, 'objects', []):
            if obj.cell == (x,y) and obj.type == 'door':
                return obj.state == 'open'
        return True

    def notify(self, kind, message, obj=None, puzzle_id=None):
        self.feedback, self.feedback_time = kind, .7
        position = self.center(obj.cell) if obj else self.position
        self.events.append({'kind':kind, 'position':tuple(position),
                            'object_id':obj.id if obj else None,
                            'puzzle_id':puzzle_id or (obj.puzzle_id if obj else None)})
        self.say(message)

    def return_to_body(self):
        restored = self.mode.return_to_alive()
        if restored is None:
            self.notify('wrong','Plus de potions de resurrection. Attendez la fin du temps fantome.')
            return
        self.position.update(restored)
        self.cooldown = 5.0
        self.previous_path_cell = None
        self.notify('return','Retour au corps. Poison disponible dans 5 secondes.')

    def action(self, key):
        if self.won or self.lost: return
        if key in (pygame.K_p, pygame.K_RETURN) and self.ghost:
            self.return_to_body()
        elif key == pygame.K_p:
            if self.cooldown:
                self.say(f'Poison en recharge : {self.cooldown:.1f} s.')
            elif self.mode.enter_ghost_mode(self.position):
                self.notify('transform','Observez les indices. P ou Entree consomme une potion de resurrection.')
            else:
                self.notify('wrong','Plus de poisons. Ouvrez un coffre gagne pour en recuperer.')
        elif key == pygame.K_e:
            if self.ghost:
                self.say('Le fantome observe mais ne peut pas agir sur les objets.')
                return
            nearby = [o for o in self.objects if o.type in ('statue','lever','door','sign','chest') and (o.type != 'chest' or o.state == 'closed') and self.center(o.cell).distance_to(self.position) <= 23]
            if nearby:
                min(nearby,key=lambda o:self.center(o.cell).distance_to(self.position)).interact(self)

    def interact_object(self, obj):
        if self.ghost: return 'blocked'
        if obj.type == 'sign':
            self.say(obj.text)
            return 'read'
        if obj.type == 'door':
            if obj.state == 'open': return 'open'
            if set(obj.required_keys) <= self.keys:
                obj.state = 'open'
                self.notify('door','La porte est ouverte.',obj)
                return 'open'
            self.notify('wrong','La porte est verrouillee. Il manque une cle.')
            return 'locked'
        if obj.type == 'chest':
            if obj.state != 'closed' or not self.puzzles.puzzles[obj.puzzle_id].solved:
                return 'locked'
            obj.state = 'open'
            self.mode.poison_potions.count += obj.loot.get('poison',0)
            self.mode.resurrection_potions.count += obj.loot.get('resurrection',0)
            key = next(o for o in self.objects if o.type == 'key' and o.puzzle_id == obj.puzzle_id)
            self.key_ready_at[key.id] = self.time + .65
            self.notify('chest',f"Coffre ouvert : +{obj.loot.get('poison',0)} poison, +{obj.loot.get('resurrection',0)} resurrection.",obj)
            return 'opened'
        if obj.type == 'key':
            puzzle = self.puzzles.puzzles[obj.puzzle_id]
            if not puzzle.solved or obj.state == 'collected' or self.time < self.key_ready_at.get(obj.id,float('inf')): return 'locked'
            obj.state = 'collected'
            self.keys.add(obj.key_id)
            self.keys_collected = len(self.keys)
            self.collected_key_positions.add(obj.cell)
            self.notify('key',f'Cle {obj.key_id} obtenue ! {len(self.keys)}/3.',obj)
            return 'collected'
        if obj.type in ('statue','lever'):
            result = self.puzzles.submit(obj.puzzle_id,obj.id)
            self.apply_result(obj.puzzle_id,result)
            return result
        return 'blocked'

    def apply_result(self, puzzle_id, result):
        puzzle = self.puzzles.puzzles[puzzle_id]
        for obj in self.objects:
            if obj.puzzle_id == puzzle_id and obj.type in ('statue','lever'):
                obj.state = 'active' if obj.id in puzzle.current_sequence else 'idle'
        messages = {'unobserved':'Les indices vous echappent. Observez-les en fantome.',
                    'correct':'Bonne activation ! Continuez dans le bon ordre.',
                    'wrong':'Mauvais ordre. La sequence recommence, sans perte.',
                    'solved':'Le sanctuaire repond ! Un coffre apparait. E pour l ouvrir.'}
        if result == 'solved':
            chest = next(o for o in self.objects if o.type == 'chest' and o.puzzle_id == puzzle_id)
            chest.state = 'closed'
        if result in messages:
            self.notify('wrong' if result in ('wrong','unobserved') else result,messages[result],puzzle_id=puzzle_id)

    def reset_path(self):
        self.puzzles.reset('path_green')
        self.position.update(self.center(self.data['danger_room']['reset_cell']))
        self.previous_path_cell = None
        self.notify('wrong','Mauvaise dalle : retour a l entree de la salle. Vos cles sont conservees.')

    def process_cell(self):
        if self.ghost:
            for obj in self.objects:
                if obj.type in ('clue','footprint') and self.center(obj.cell).distance_to(self.position) <= 24:
                    if self.puzzles.observe(obj.puzzle_id,obj.id,True):
                        self.notify('clue',obj.text or 'Suivez le courant des empreintes. Retenez ses detours.',obj)
            nearby=[o for o in self.objects if o.type=='clue' and self.center(o.cell).distance_to(self.position)<=20]
            if nearby:
                nearest=min(nearby,key=lambda o:self.center(o.cell).distance_to(self.position))
                self.say(nearest.text)
            return
        path = self.puzzles.puzzles['path_green']
        danger = pygame.Rect(self.data['danger_room']['rect'])
        if danger.collidepoint(self.cell) and not path.solved:
            if self.previous_path_cell != self.cell:
                self.previous_path_cell = self.cell
                footprint = next((o for o in self.objects if o.type == 'footprint' and o.cell == self.cell),None)
                result = self.puzzles.submit('path_green',footprint.id if footprint else 'trap')
                if result in ('wrong','unobserved'):
                    self.reset_path()
                    return
                if result in ('correct','solved'): self.apply_result('path_green',result)
        elif not danger.collidepoint(self.cell):
            if path.current_sequence and not path.solved: self.puzzles.reset('path_green')
            self.previous_path_cell = None
        for obj in self.objects:
            if obj.type == 'key' and obj.cell == self.cell: obj.interact(self)
        if self.tile(*self.cell) == 'E' and {'blue','red','green'} <= self.keys:
            self.won = True
            self.notify('solved','Trois mondes compris. Le sanctuaire vous laisse partir !')

    def update(self, dt, direction=(0,0)):
        if self.won or self.lost: return
        dt = max(0,dt)
        self.time += dt
        self.message_time = max(0,self.message_time-dt)
        self.feedback_time = max(0,self.feedback_time-dt)
        if not self.ghost: self.cooldown = max(0,self.cooldown-dt)
        restored = self.mode.update(dt)
        if self.dead:
            self.lost = True
            self.notify('wrong','Le temps est ecoule : vous etes mort. N pour recommencer.')
            return
        if restored is not None:
            self.position.update(restored)
            self.cooldown = 5.0
            self.previous_path_cell = None
            self.notify('return','Le temps est ecoule : retour au corps sans consommer de potion.')
        direction = pygame.Vector2(direction)
        if direction.length_squared(): direction = direction.normalize()
        move = direction * (78 if self.ghost else 65)*dt
        steps = max(1,math.ceil(move.length()/3))
        for _ in range(steps):
            for axis in ('x','y'):
                candidate = self.position.copy()
                setattr(candidate,axis,getattr(candidate,axis)+getattr(move/steps,axis))
                if not self.blocked(candidate): self.position.update(candidate)
            if self.holes.is_lethal(self.cell):
                self.mode.die()
                self.lost = True
                self.notify('wrong','Un trou spectral vous a englouti.')
                return
            old = self.position.copy()
            self.process_cell()
            if self.position != old: break
