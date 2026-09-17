"""Les trois enigmes du sanctuaire : observer mort, resoudre vivant."""
import math
import random
from pathlib import Path
import pygame
from systems.training_level import TrainingLevel
from systems.puzzle_manager import PuzzleManager
from entities.puzzle_object import PuzzleObject

MAP_PATH = Path(__file__).resolve().parents[1] / 'assets/maps/sanctuaire_enigmes.json'

# Emplacements des quatre statues a toucher dans l'ordre, relatifs a
# l'origine de la salle speciale qui les accueille.
STATUE_OFFSETS = [(1, 1), (4, 1), (1, 4), (4, 4)]
STATUE_REWARD_OFFSET = (2, 3)

# Plateau de dalles (4x4) pour l'epreuve du chemin : position fixe par salle,
# a l'ecart du coffre leurre (qui reste hors du plateau, juste a cote).
PATH_LAYOUT = {
    'NW': {'decoy': (13, 14), 'plateau': pygame.Rect(11, 10, 4, 4)},
    'NE': {'decoy': (37, 14), 'plateau': pygame.Rect(35, 10, 4, 4)},
    'W':  {'decoy': (9, 25), 'plateau': pygame.Rect(5, 23, 4, 4)},
}


def generate_path(rng, rect, anchor, length=8, attempts=25):
    """Marche aleatoire auto-evitante dans une salle entierement ouverte : la
    premiere dalle est toujours juste a cote de l'ancre (le coffre leurre),
    jamais dessus ni loin. Plusieurs essais, on garde le plus long obtenu si
    la longueur visee n'est jamais atteinte (salle trop petite ou impasse
    rapide)."""
    cells = [(x, y) for x in range(rect.x, rect.x+rect.w) for y in range(rect.y, rect.y+rect.h)
             if (x, y) != anchor]
    cellset = set(cells)
    starts = [(anchor[0]+dx, anchor[1]+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
              if (anchor[0]+dx, anchor[1]+dy) in cellset]
    if not starts: starts = cells
    best = []
    for _ in range(attempts):
        start = rng.choice(starts)
        path = [start]
        visited = {start}
        while len(path) < length:
            x, y = path[-1]
            options = [(x+dx, y+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
                       if (x+dx, y+dy) in cellset and (x+dx, y+dy) not in visited]
            if not options: break
            nxt = rng.choice(options)
            path.append(nxt); visited.add(nxt)
        if len(path) > len(best): best = path
        if len(best) >= length: break
    return best


class PuzzleLevel(TrainingLevel):
    def __init__(self, path=MAP_PATH, seed=None):
        super().__init__(path, hole_count=0)
        # Rester fantome jusqu'au bout du temps TUE : c'est la seule facon de
        # perdre ici, puisqu'il n'y a plus de pieges. A True, le fantome etait
        # simplement ramene a son corps et la partie devenait impossible a
        # perdre (voir GhostModeController.update()).
        self.mode.auto_return_on_timeout = False
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
        self.wall_hits = {}
        self.statue_motion = {}
        self.statue_bounds = {'statue': pygame.Rect(36,35,3,3)}
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
        self.objects.append(PuzzleObject('future_door','door',(25,9),required_keys=['gold']))
        # Trois salles scellees (auparavant vides) : une clef doree au hasard de
        # l'une des trois, les deux autres cachent l'epreuve des statues (dans
        # l'ordre indique par les inscriptions spectrales) ou du chemin invisible
        # (observe fantome, reproduit vivant). Une clef argentee (ressource
        # consommable, pas un badge permanent) ouvre UNE porte au choix parmi
        # celles encore fermees ; une epreuve reussie rend une clef argentee
        # pour retenter sa chance sur une autre salle.
        self.special_rooms = {'NW': pygame.Rect(10,10,6,6), 'NE': pygame.Rect(34,10,6,6), 'W': pygame.Rect(5,22,7,6)}
        special_entry = {'NW': (13,16), 'NE': (37,16), 'W': (11,25)}
        self.special_order = rng.sample(list(self.special_rooms), 3)
        gold_room = rng.choice(self.special_order)
        trial_rooms = [r for r in self.special_order if r != gold_room]
        trial_kinds = rng.sample(['statues', 'path'], 2)
        self.special_content = {gold_room: 'gold', **dict(zip(trial_rooms, trial_kinds))}
        self.special_pid = {r: k+'_sp' for r, k in self.special_content.items() if k != 'gold'}
        self.special_spawned = set()
        self.path_cells = {}
        self.path_plateau = {}
        self.path_progress = {}
        self.path_last_cell = {}
        for room in self.special_order:
            rect = self.special_rooms[room]
            center = (rect.x+rect.w//2, rect.y+rect.h//2)
            self.objects.append(PuzzleObject('special_entry_'+room, 'door', special_entry[room],
                required_keys=['silver'], text='special_door'))
            if self.special_content[room] == 'gold':
                self.objects.append(PuzzleObject(room+'_goldchest', 'chest', center, state='closed', text='gold',
                    loot={'poison': 1, 'resurrection': 1}))
                self.objects.append(PuzzleObject(room+'_goldkey', 'key', center, key_id='gold'))
            else:
                kind = self.special_content[room]
                pid = self.special_pid[room]
                if kind == 'path':
                    decoy_cell = PATH_LAYOUT[room]['decoy']
                else:
                    decoy_cell = center
                self.objects.append(PuzzleObject(room+'_decoy', 'chest', decoy_cell, state='closed', text=room))
                if kind == 'statues':
                    members = [pid+'_'+str(i) for i in range(4)]
                    definitions.append(dict(id=pid, type='sequence', members=members,
                        reward={'type': 'key', 'id': 'silver'}, required_clues=members))
                else:
                    plateau = PATH_LAYOUT[room]['plateau']
                    self.path_plateau[pid] = plateau
                    self.path_cells[pid] = generate_path(rng, plateau, decoy_cell)
                    definitions.append(dict(id=pid, type='physical', solution=[], reward={'type': 'key', 'id': 'silver'}))
        self.puzzles = PuzzleManager(definitions, seed=seed)
        self.puzzles.puzzles['tomb'].solution = ['tomb_'+str(self.targets['tomb'])]
        self.puzzles.puzzles['statue'].solution = ['moving_statue']
        self.puzzles.puzzles['wall'].solution = ['wall_'+str(self.targets['wall'])]
        # Conserver la desactivation des trous introduite sur main.
        self.time = 0.0
        self.key_ready_at = {}
        self.keys = set()
        self.silver_keys = 0
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

    @property
    def special_room(self):
        return next((name for name,rect in self.special_rooms.items() if rect.collidepoint(self.cell)), None)

    def special_room_hidden(self, cell):
        """Vrai si `cell` appartient a une salle speciale dans laquelle le
        joueur ne se trouve pas physiquement en ce moment : le contenu
        (coffre, epreuve, cle) et sa solution restent invisibles depuis
        l'exterieur - meme en fantome, meme juste a cote - tant qu'on n'est
        pas entre dans cette salle precise. Seule la porte (sa couleur)
        echappe a cette regle, donc le rendu doit excepter les objets de type
        'door'. Des qu'on ressort, le contenu redevient invisible : rien n'est
        memorise d'une visite a l'autre."""
        room = next((r for r,rect in self.special_rooms.items() if rect.collidepoint(cell)), None)
        return room is not None and room != self.special_room

    def _spawn_special_trial(self, room):
        if room in self.special_spawned: return
        self.special_spawned.add(room)
        kind = self.special_content[room]
        pid = self.special_pid[room]
        rect = self.special_rooms[room]
        ox, oy = rect.x, rect.y
        # La salle se referme sur l'epreuve : on ne peut plus sortir (ni y
        # entrer) tant qu'elle n'est pas resolue.
        door = next(o for o in self.objects if o.id == 'special_entry_'+room)
        door.state = 'closed'
        if kind == 'statues':
            for i,(dx,dy) in enumerate(STATUE_OFFSETS):
                self.objects.append(PuzzleObject(pid+'_'+str(i),'order_statue',(ox+dx,oy+dy),pid))
            rx,ry = STATUE_REWARD_OFFSET
            reward_cell = (ox+rx, oy+ry)
        else:
            plateau = self.path_plateau[pid]
            for gx in range(plateau.x, plateau.x+plateau.w):
                for gy in range(plateau.y, plateau.y+plateau.h):
                    self.objects.append(PuzzleObject(f'{pid}_tile_{gx}_{gy}','plateau',(gx,gy),pid,
                        interaction_allowed=False))
            path = self.path_cells[pid]
            for i,cell in enumerate(path):
                self.objects.append(PuzzleObject(pid+'_fp_'+str(i),'footprint',cell,pid,
                    interaction_allowed=False, visible_state='ghost'))
            self.path_progress[pid] = 0
            self.path_last_cell[pid] = None
            reward_cell = path[-1]
        self.objects.append(PuzzleObject(pid+'_chest','chest',reward_cell,pid,state='hidden',
            loot={'poison':1,'resurrection':1}))
        self.objects.append(PuzzleObject(pid+'_key','key',reward_cell,pid,
            key_id=self.puzzles.puzzles[pid].reward['id']))
        self.notify('transform','Un mecanisme cache se revele : une epreuve apparait dans la salle !',None,puzzle_id=pid)

    def _interact_special_chest(self, obj):
        if obj.state != 'closed': return 'locked'
        if obj.text == 'gold':
            obj.state = 'open'
            self.mode.poison_potions.count += obj.loot.get('poison',0)
            self.mode.resurrection_potions.count += obj.loot.get('resurrection',0)
            key = next(o for o in self.objects if o.type == 'key' and o.cell == obj.cell)
            self.key_ready_at[key.id] = self.time + .65
            self.notify('chest','Un eclat dore : la clef doree est a vous !',obj)
            return 'opened'
        obj.state = 'hidden'
        self.notify('chest','Le coffre etait un leurre et disparait. La salle se referme derriere vous.',obj)
        self._spawn_special_trial(obj.text)
        return 'empty'

    def _reveal_reward(self, pid, obj):
        next(o for o in self.objects if o.id == pid+'_chest').state = 'closed'
        room = next((r for r,p in self.special_pid.items() if p == pid), None)
        if room:
            door = next(o for o in self.objects if o.id == 'special_entry_'+room)
            door.state = 'open'
        self.notify('solved', 'Le mecanisme cede ! Ouvrez le coffre avec E.', obj)

    def solve(self, pid, obj):
        puzzle = self.puzzles.puzzles[pid]
        if puzzle.solved: return
        puzzle.solved = True
        self.puzzles.rewards.append(dict(puzzle.reward))
        self._reveal_reward(pid, obj)

    def _advance_path(self, pid):
        plateau = self.path_plateau[pid]
        if not plateau.collidepoint(self.cell): return
        path = self.path_cells[pid]
        if self.path_last_cell.get(pid) == self.cell: return
        self.path_last_cell[pid] = self.cell
        progress = self.path_progress.get(pid,0)
        if self.cell == path[progress]:
            progress += 1
            self.path_progress[pid] = progress
            if progress == len(path):
                self.solve(pid, next(o for o in self.objects if o.id == pid+'_chest'))
            else:
                self.notify('correct', f'Bon pas ({progress}/{len(path)}).', None, puzzle_id=pid)
        elif self.cell in path[:progress]:
            return
        else:
            self.path_progress[pid] = 0
            self.position.update(self.center(path[0]))
            self.notify('wrong','Mauvaise dalle : retour au debut du chemin.', None, puzzle_id=pid)

    def passable(self, x, y, ghost=None):
        ghost = self.ghost if ghost is None else ghost
        tile = self.tile(x,y)
        if tile == '#': return False
        if tile == 'Y': return ghost
        for obj in getattr(self, 'objects', []):
            if obj.cell == (x,y):
                if obj.type == 'door': return obj.state == 'open'
                if obj.type == 'wall': return obj.state == 'broken'
                if obj.type in ('tomb','statue','order_statue') and not ghost: return False
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
            nearby = [o for o in self.objects if o.type in ('statue','tomb','wall','door','sign','chest','order_statue') and (o.type != 'chest' or o.state == 'closed') and (o.type != 'door' or o.state != 'open') and self.center(o.cell).distance_to(self.position) <= 23]
            if nearby:
                min(nearby,key=lambda o:self.center(o.cell).distance_to(self.position)).interact(self)

    def interact_object(self, obj):
        if self.ghost: return 'blocked'
        if obj.type == 'sign':
            self.say(obj.text)
            return 'read'
        if obj.type == 'door':
            if obj.state == 'open': return 'open'
            if obj.text == 'special_door':
                if self.silver_keys <= 0:
                    self.notify('wrong','La porte est verrouillee. Il faut une clef argentee.')
                    return 'locked'
                self.silver_keys -= 1
                obj.state = 'open'
                self.notify('door','La porte est ouverte. La clef argentee est depensee.',obj)
                return 'open'
            if set(obj.required_keys) <= self.keys:
                obj.state = 'open'
                self.notify('door','La porte est ouverte.',obj)
                return 'open'
            self.notify('wrong','La porte est verrouillee. Il manque une cle.')
            return 'locked'
        if obj.type == 'chest':
            if obj.puzzle_id is None:
                return self._interact_special_chest(obj)
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
            if obj.puzzle_id is not None and not self.puzzles.puzzles[obj.puzzle_id].solved:
                return 'locked'
            if obj.state == 'collected' or self.time < self.key_ready_at.get(obj.id,float('inf')): return 'locked'
            obj.state = 'collected'
            self.collected_key_positions.add(obj.cell)
            if obj.key_id == 'silver':
                self.silver_keys += 1
                self.notify('key','Clef argentee obtenue ! Ouvrez une salle scellee encore fermee.',obj)
                return 'collected'
            self.keys.add(obj.key_id)
            self.keys_collected = len(self.keys)
            color_name={'blue':'bleue','red':'rouge','green':'verte','gold':'doree'}[obj.key_id]
            if obj.key_id == 'gold':
                message = 'Clef doree obtenue ! La porte scellee du Nord est desormais accessible.'
            else:
                message = f'Cle {color_name} obtenue ! Cherchez la porte de meme couleur sur M.'
            self.notify('key',message,obj)
            return 'collected'
        if obj.type == 'tomb':
            if obj.id == obj.puzzle_id+'_'+str(self.targets[obj.puzzle_id]):
                obj.state = 'open'
                self.solve(obj.puzzle_id, obj)
                return 'solved'
            obj.state = 'searched'
            self.notify('wrong', 'Cette tombe est vide. Une aura guide les fantomes.', obj)
            return 'wrong'
        if obj.type == 'wall':
            if obj.state == 'broken': return 'open'
            if obj.id != obj.puzzle_id+'_'+str(self.targets[obj.puzzle_id]):
                self.notify('wrong', 'La pierre resiste. Cherchez la fissure en fantome.', obj)
                return 'wrong'
            hits = self.wall_hits.get(obj.puzzle_id,0) + 1
            self.wall_hits[obj.puzzle_id] = hits
            if hits >= 3:
                obj.state = 'broken'
                self.solve(obj.puzzle_id, obj)
                return 'solved'
            self.notify('correct', f'CRAC ! La pierre se fissure ({hits}/3).', obj)
            return 'correct'
        if obj.type == 'statue':
            if self.puzzles.puzzles[obj.puzzle_id].solved: return 'already_solved'
            delta = self.center(obj.cell)-self.position
            if abs(delta.x)>abs(delta.y): direction=(1 if delta.x>0 else -1,0)
            else: direction=(0,1 if delta.y>0 else -1)
            target=(obj.cell[0]+direction[0],obj.cell[1]+direction[1])
            # Garder une couronne libre pour toujours pouvoir contourner la statue.
            if not self.statue_bounds[obj.puzzle_id].collidepoint(target):
                self.say('Limite du socle. Contournez la statue pour la pousser autrement.')
                return 'blocked'
            self.statue_motion[obj.id]=(obj.cell,target,self.time)
            obj.cell=target
            self.notify('correct', 'La statue glisse sur les dalles.', obj)
            if target == self.targets[obj.puzzle_id]:
                obj.state='active'
                self.solve(obj.puzzle_id,obj)
                return 'solved'
            return 'correct'
        if obj.type == 'order_statue':
            result = self.puzzles.submit(obj.puzzle_id, obj.id, ghost=False)
            if result == 'solved':
                self._reveal_reward(obj.puzzle_id, obj)
            elif result == 'correct':
                self.notify('correct','La statue repond. Poursuivez dans le bon ordre.', obj)
            elif result == 'wrong':
                self.notify('wrong','Mauvais ordre : la sequence se reinitialise.', obj)
            elif result == 'unobserved':
                self.notify('wrong','Observez toutes les inscriptions en mode fantome avant toute action.')
            return result
        return 'blocked'

    TRIAL_HINTS = {
        'tomb': 'La tombe cachee : P revele une aura. Revenez vivant et fouillez avec E.',
        'statue': 'Le gardien : P revele le socle. Vivant, placez-vous derriere la statue et poussez avec E.',
        'wall': 'Le mur condamne : cherchez la rune avec P. Vivant, frappez trois fois avec E.',
        'special': 'Salle scellee : un coffre scintille au fond, mais la prudence reste de mise.',
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
        special = self.special_room
        zone = room or ('special' if special else None)
        self.last_room = zone
        self.show_trial_hint(zone)
        if self.ghost:
            for obj in self.objects:
                if (obj.type == 'order_statue' and not self.special_room_hidden(obj.cell)
                        and self.center(obj.cell).distance_to(self.position) <= 40):
                    if self.puzzles.observe(obj.puzzle_id, obj.id, ghost=True):
                        rank = self.puzzles.puzzles[obj.puzzle_id].solution.index(obj.id)+1
                        self.notify('clue', f'Inscription spectrale : rang {rank}.', obj)
            return
        for obj in self.objects:
            if obj.type == 'key' and obj.cell == self.cell: obj.interact(self)
        if special and self.special_content.get(special) == 'path':
            pid = self.special_pid.get(special)
            if pid and special in self.special_spawned and not self.puzzles.puzzles[pid].solved:
                self._advance_path(pid)
        if self.tile(*self.cell) == 'E':
            self.won = True
            self.say('La clef doree a force la porte du Nord : vous avez triomphe du sanctuaire !')

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
