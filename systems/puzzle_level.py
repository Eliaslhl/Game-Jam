"""Les trois enigmes du sanctuaire : observer mort, resoudre vivant."""
import math
import random
from pathlib import Path
import pygame
from systems.training_level import TrainingLevel
from systems.puzzle_manager import PuzzleManager
from entities.puzzle_object import PuzzleObject

MAP_PATH = Path(__file__).resolve().parents[1] / 'assets/maps/sanctuaire_enigmes.json'


class PuzzleLevel(TrainingLevel):
    def __init__(self, path=MAP_PATH, seed=None):
        super().__init__(path, hole_count=0)
        self.mode.auto_return_on_timeout = True
        rng = random.Random(seed)
        self.rooms = {'tomb': pygame.Rect(10,34,6,6),
                      'statue': pygame.Rect(35,34,5,5),
                      'wall': pygame.Rect(39,22,5,6)}
        self.order = rng.sample(list(self.rooms), 3)
        colors = rng.sample(['blue', 'red', 'green'], 2)
        self.entry_cells = {'tomb': (13,33), 'statue': (37,33), 'wall': (39,25)}
        self.objects = []
        definitions = []
        self.targets = {'tomb': rng.randrange(5), 'statue': rng.choice([(36,35),(37,35),(38,35)]),
                        'wall': rng.randrange(3)}
        self.wall_hits = 0
        self.statue_motion = None
        self.last_room = None
        # Consigne de l'epreuve en cours, pour pouvoir l'effacer en sortant de la
        # salle (voir show_trial_hint).
        self._trial_hint = None
        # Fermer l'ancien acces spectral lateral et l'ancienne sortie du jardin.
        for x,y in [(44,24),(39,39)]:
            row=list(self.grid[y]); row[x]='#'; self.grid[y]=''.join(row)
        for i,pid in enumerate(self.order):
            reward = colors[i] if i < 2 else 'silver'
            definitions.append(dict(id=pid,type='physical',solution=[],reward={'type':'key','id':reward}))
            self.objects.append(PuzzleObject('entry_'+pid,'door',self.entry_cells[pid],
                state='open' if i==0 else 'closed', required_keys=[] if i==0 else [colors[i-1]]))
            cell={'tomb':(13,38),'statue':(37,37),'wall':(41,22)}[pid]
            self.objects.extend([PuzzleObject(pid+'_chest','chest',cell,pid,state='hidden',loot={'poison':1,'resurrection':1}),
                                 PuzzleObject(pid+'_key','key',cell,pid,key_id=reward)])
        for i in range(5):
            self.objects.append(PuzzleObject('tomb_'+str(i),'tomb',(10+i,35),'tomb'))
        self.objects.append(PuzzleObject('moving_statue','statue',(37,37),'statue'))
        for i,x in enumerate((36,37,38)):
            self.objects.append(PuzzleObject('socket_'+str(i),'socket',(x,35),'statue',interaction_allowed=False))
        for i,x in enumerate((40,41,42)):
            self.objects.append(PuzzleObject('wall_'+str(i),'wall',(x,23),'wall'))
        # Le coffre du mur est derriere une cloison complete, sans contournement.
        row=list(self.grid[23]); row[39]=row[43]='#'; self.grid[23]=''.join(row)
        self.objects.append(PuzzleObject('future_door','door',(25,9),required_keys=['silver'],text='future'))
        self.puzzles = PuzzleManager(definitions, seed=seed)
        self.puzzles.puzzles['tomb'].solution = ['tomb_'+str(self.targets['tomb'])]
        self.puzzles.puzzles['statue'].solution = ['moving_statue']
        self.puzzles.puzzles['wall'].solution = ['wall_'+str(self.targets['wall'])]
        # Conserver la desactivation des trous introduite sur main.
        self.time = 0.0
        self.key_ready_at = {}
        self.keys = set()
        self.keys_total = 3
        self.cooldown = 0.0
        self.events = []
        self.feedback = ''
        self.feedback_time = 0.0
        self.mode.poison_potions.count = 3
        self.mode.resurrection_potions.count = 3
        self.say('Zones jaunes sur la carte (M). P : fantome. E : fouiller, pousser ou frapper.')

    @property
    def trial_room(self):
        return next((pid for pid,rect in self.rooms.items() if rect.collidepoint(self.cell)), None)

    def solve(self, pid, obj):
        puzzle = self.puzzles.puzzles[pid]
        if puzzle.solved: return
        puzzle.solved = True
        self.puzzles.rewards.append(dict(puzzle.reward))
        next(o for o in self.objects if o.id == pid+'_chest').state = 'closed'
        self.notify('solved', 'Le mecanisme cede ! Ouvrez le coffre avec E.', obj)

    def passable(self, x, y, ghost=None):
        ghost = self.ghost if ghost is None else ghost
        tile = self.tile(x,y)
        if tile == '#': return False
        if tile == 'Y': return ghost
        for obj in getattr(self, 'objects', []):
            if obj.cell == (x,y):
                if obj.type == 'door': return obj.state == 'open'
                if obj.type == 'wall': return obj.state == 'broken'
                if obj.type in ('tomb','statue') and not ghost: return False
        return True

    def notify(self, kind, message, obj=None, puzzle_id=None):
        self.feedback, self.feedback_time = kind, .7
        position = self.center(obj.cell) if obj else self.position
        self.events.append({'kind':kind, 'position':tuple(position),
                            'object_id':obj.id if obj else None,
                            'puzzle_id':puzzle_id or (obj.puzzle_id if obj else None)})
        self.say(message)

    def return_to_body(self):
        # Position actuelle (fantome), pas celle du corps laisse en buvant le
        # poison : on ressuscite la ou on se trouve, pas la ou on est mort.
        destination = self.position.copy()
        if not self.passable(*self.cell, ghost=False):
            cx,cy=self.cell
            candidates=[(cx+dx,cy+dy) for dx,dy in ((0,1),(0,-1),(1,0),(-1,0))
                        if self.passable(cx+dx,cy+dy,ghost=False)]
            if not candidates:
                self.say('Eloignez-vous du decor pour reprendre vie.')
                return
            destination=self.center(candidates[0])
        restored = self.mode.return_to_alive(destination)
        if restored is None:
            self.notify('wrong','Plus de potions de resurrection. Attendez la fin du temps fantome.')
            return
        self.position.update(restored)
        self.cooldown = 5.0
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
            nearby = [o for o in self.objects if o.type in ('statue','tomb','wall','door','sign','chest') and (o.type != 'chest' or o.state == 'closed') and (o.type != 'door' or o.state != 'open') and self.center(o.cell).distance_to(self.position) <= 23]
            if nearby:
                min(nearby,key=lambda o:self.center(o.cell).distance_to(self.position)).interact(self)

    def interact_object(self, obj):
        if self.ghost: return 'blocked'
        if obj.type == 'sign':
            self.say(obj.text)
            return 'read'
        if obj.type == 'door':
            if obj.state == 'open': return 'open'
            if obj.text == 'future':
                self.say('Cle argentee conservee. Cette porte speciale sera disponible plus tard.')
                return 'locked'
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
            color_name={'blue':'bleue','red':'rouge','green':'verte','silver':'argentee'}[obj.key_id]
            message = ('Cle argentee obtenue ! Conservez-la pour la future porte speciale.' if obj.key_id=='silver'
                       else f'Cle {color_name} obtenue ! Cherchez la porte de meme couleur sur M.')
            self.notify('key',message,obj)
            return 'collected'
        if obj.type == 'tomb':
            if obj.id == 'tomb_'+str(self.targets['tomb']):
                obj.state = 'open'
                self.solve('tomb', obj)
                return 'solved'
            obj.state = 'searched'
            self.notify('wrong', 'Cette tombe est vide. Une aura guide les fantomes.', obj)
            return 'wrong'
        if obj.type == 'wall':
            if obj.state == 'broken': return 'open'
            if obj.id != 'wall_'+str(self.targets['wall']):
                self.notify('wrong', 'La pierre resiste. Cherchez la fissure en fantome.', obj)
                return 'wrong'
            self.wall_hits += 1
            if self.wall_hits >= 3:
                obj.state = 'broken'
                self.solve('wall', obj)
                return 'solved'
            self.notify('correct', f'CRAC ! La pierre se fissure ({self.wall_hits}/3).', obj)
            return 'correct'
        if obj.type == 'statue':
            if self.puzzles.puzzles['statue'].solved: return 'already_solved'
            delta = self.center(obj.cell)-self.position
            if abs(delta.x)>abs(delta.y): direction=(1 if delta.x>0 else -1,0)
            else: direction=(0,1 if delta.y>0 else -1)
            target=(obj.cell[0]+direction[0],obj.cell[1]+direction[1])
            # Garder une couronne libre pour toujours pouvoir contourner la statue.
            if not pygame.Rect(36,35,3,3).collidepoint(target):
                self.say('Limite du socle. Contournez la statue pour la pousser autrement.')
                return 'blocked'
            self.statue_motion=(obj.cell,target,self.time)
            obj.cell=target
            self.notify('correct', 'La statue glisse sur les dalles.', obj)
            if target == self.targets['statue']:
                obj.state='active'
                self.solve('statue',obj)
                return 'solved'
            return 'correct'
        return 'blocked'

    TRIAL_HINTS = {
        'tomb': 'La tombe cachee : P revele une aura. Revenez vivant et fouillez avec E.',
        'statue': 'Le gardien : P revele le socle. Vivant, placez-vous derriere la statue et poussez avec E.',
        'wall': 'Le mur condamne : cherchez la rune avec P. Vivant, frappez trois fois avec E.',
    }

    def show_trial_hint(self, room):
        """La consigne de l'epreuve reste sur le parchemin tant qu'on est dans la
        salle, et disparait des qu'on en sort - plutot que de defiler six secondes
        puis de laisser le joueur sans rappel au milieu de l'enigme.

        Elle ne recouvre jamais un message qui vient d'arriver (cle obtenue, mur
        qui se fissure, porte verrouillee) : celui-la passe d'abord, et la
        consigne revient quand il s'efface."""
        if room is None:
            if self._trial_hint is not None and self.message == self._trial_hint:
                self.message_time = 0
            self._trial_hint = None
            return
        self._trial_hint = self.TRIAL_HINTS[room]
        if self.message_time <= 0 or self.message in self.TRIAL_HINTS.values():
            self.say(self._trial_hint)

    def process_cell(self):
        room = self.trial_room
        self.last_room = room
        self.show_trial_hint(room)
        if self.ghost: return
        for obj in self.objects:
            if obj.type == 'key' and obj.cell == self.cell: obj.interact(self)

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
