"""Parcours des trois salles dans les six ordres, et interdictions d'etat."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import deque
from itertools import permutations
import unittest
import pygame
from systems.puzzle_level import PuzzleLevel
from views.puzzle_view import PuzzleGame, SIZE


def walk(level,target):
    target=tuple(target); start=level.cell
    pending=deque([start]);parents={start:None}
    while pending:
        cell=pending.popleft()
        if cell==target:break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            n=(cell[0]+dx,cell[1]+dy)
            if n not in parents and level.passable(*n):parents[n]=cell;pending.append(n)
    if target not in parents:raise AssertionError(f'Pas de chemin {start} -> {target}')
    path=[];cell=target
    while parents[cell] is not None:path.append(cell);cell=parents[cell]
    for cell in reversed(path):
        delta=level.center(cell)-level.position
        level.update(delta.length()/(78 if level.ghost else 65),delta)
        if level.position.distance_to(level.center(cell))>.01:raise AssertionError(f'Bloque vers {cell} : {level.cell}')


class PuzzleTests(unittest.TestCase):
    def solve(self,level,pid):
        stage={'statues_blue':(13,36),'path_green':(37,33),'levers_red':(43,24)}[pid]
        walk(level,stage)
        level.update(5);level.action(pygame.K_p)
        for clue in [o for o in level.objects if o.puzzle_id==pid and o.type in ('clue','footprint')]:
            walk(level,clue.cell)
        self.assertTrue(level.ghost)
        self.assertFalse(level.puzzles.puzzles[pid].solved)
        level.action(pygame.K_RETURN)
        puzzle=level.puzzles.puzzles[pid]
        for oid in puzzle.solution:
            obj=next(o for o in level.objects if o.id==oid)
            walk(level,obj.cell)
            if obj.type != 'footprint':level.action(pygame.K_e)
        self.assertTrue(puzzle.solved)
        key=next(o for o in level.objects if o.puzzle_id==pid and o.type=='key')
        walk(level,key.cell)
        self.assertNotIn(key.key_id,level.keys)
        level.action(pygame.K_e)
        level.update(.7)
        self.assertIn(key.key_id,level.keys)

    def test_all_six_orders_and_exit(self):
        for order in permutations(['statues_blue','path_green','levers_red']):
            with self.subTest(order=order):
                level=PuzzleLevel()
                for pid in order:self.solve(level,pid)
                walk(level,(25,10));level.action(pygame.K_e)
                walk(level,(25,6))
                self.assertTrue(level.won)
                self.assertEqual(len(level.keys),3)

    def test_visibility_ghost_interaction_and_wrong_reset(self):
        level=PuzzleLevel()
        statue=next(o for o in level.objects if o.id==level.puzzles.puzzles['statues_blue'].solution[0])
        clue=next(o for o in level.objects if o.id=='number_1')
        self.assertFalse(clue.visible_to(level))
        self.assertEqual(statue.interact(level),'unobserved')
        level.action(pygame.K_p)
        self.assertTrue(clue.visible_to(level))
        self.assertEqual(statue.interact(level),'blocked')
        key=next(o for o in level.objects if o.type=='key')
        self.assertEqual(key.interact(level),'blocked')
        self.assertFalse(level.keys)
        for oid in level.puzzles.puzzles['statues_blue'].required_clues:
            level.puzzles.observe('statues_blue',oid,True)
        level.action(pygame.K_RETURN)
        self.assertEqual(statue.interact(level),'correct')
        self.assertEqual(statue.interact(level),'wrong')
        self.assertFalse(level.puzzles.puzzles['statues_blue'].current_sequence)
        self.assertEqual(statue.state,'idle')

    def test_path_failure_preserves_key_and_solved_state(self):
        level=PuzzleLevel();self.solve(level,'statues_blue')
        walk(level,(37,33))
        level.update(16/65,(0,1))
        self.assertEqual(level.cell,(37,33))
        self.assertIn('blue',level.keys)
        self.assertTrue(level.puzzles.puzzles['statues_blue'].solved)
        blue=next(o for o in level.objects if o.id=='blue_key')
        self.assertEqual(blue.state,'collected')
        self.assertFalse(level.puzzles.puzzles['path_green'].solved)

    def test_specific_and_final_doors(self):
        level=PuzzleLevel()
        blue=next(o for o in level.objects if o.id=='blue_door')
        final=next(o for o in level.objects if o.id=='final_door')
        self.assertEqual(blue.interact(level),'locked')
        level.keys.add('blue')
        self.assertEqual(blue.interact(level),'open')
        self.assertEqual(final.interact(level),'locked')
        level.action(pygame.K_p)
        self.assertEqual(final.interact(level),'blocked')

    def test_limited_stocks_chests_and_free_timeout(self):
        level=PuzzleLevel()
        self.assertEqual((level.mode.poison_potions.count,level.mode.resurrection_potions.count),(3,3))
        for _ in range(3):
            level.action(pygame.K_p)
            self.assertTrue(level.ghost)
            level.action(pygame.K_RETURN)
            level.update(5)
        self.assertEqual((level.mode.poison_potions.count,level.mode.resurrection_potions.count),(0,0))
        level.action(pygame.K_p)
        self.assertFalse(level.ghost)
        self.assertIn('Plus de poisons',level.message)
        level.mode.poison_potions.count=1
        level.action(pygame.K_p)
        body=level.mode.corpse_position
        level.action(pygame.K_RETURN)
        self.assertTrue(level.ghost)
        level.update(11)
        self.assertFalse(level.ghost)
        self.assertEqual(tuple(level.position),body)
        self.assertEqual(level.mode.resurrection_potions.count,0)

    def test_chest_loot_once_and_no_ghost_looting(self):
        level=PuzzleLevel()
        chest=next(o for o in level.objects if o.type=='chest')
        self.assertEqual(chest.interact(level),'locked')
        self.solve(level,chest.puzzle_id)
        self.assertEqual((level.mode.poison_potions.count,level.mode.resurrection_potions.count),(3,3))
        self.assertEqual(chest.state,'open')
        self.assertEqual(chest.interact(level),'locked')
        self.assertEqual((level.mode.poison_potions.count,level.mode.resurrection_potions.count),(3,3))
        solution=level.puzzles.puzzles[chest.puzzle_id].solution
        self.assertEqual(level.puzzles.submit(chest.puzzle_id,solution[0]),'already_solved')
        self.assertEqual(len(level.puzzles.rewards),1)
        level.update(5);level.action(pygame.K_p)
        self.assertEqual(chest.interact(level),'blocked')

    def test_random_permutations_clues_and_persistence(self):
        previous=None
        for _ in range(16):
            level=PuzzleLevel()
            solutions={p.id:tuple(p.solution) for p in level.puzzles.puzzles.values() if p.type=='sequence'}
            for pid,solution in solutions.items():
                self.assertEqual(len(solution),len(set(solution)))
                if previous:self.assertNotEqual(previous[pid],solution)
            for obj in level.objects:
                if obj.clue_target:
                    rank=level.puzzles.puzzles[obj.puzzle_id].solution.index(obj.clue_target)
                    if rank==0:self.assertIn('avant toutes',obj.text)
                    else:
                        previous_member=level.puzzles.puzzles[obj.puzzle_id].solution[rank-1].rsplit('_',1)[-1]
                        self.assertIn('apres la statue '+previous_member,obj.text)
                if obj.clue_index is not None:
                    members=[m.rsplit('_',1)[-1] for m in level.puzzles.puzzles[obj.puzzle_id].solution]
                    if obj.clue_index==0:self.assertEqual(obj.text,f'{members[0]} doit preceder {members[1]}.')
                    elif obj.clue_index==1:self.assertEqual(obj.text,f'{members[2]} attend que {members[1]} ait parle.')
                    else:self.assertEqual(obj.text,f'Le veilleur {members[0]} ouvre le rituel.')
            level.action(pygame.K_p);level.update(11);level.reset_path()
            self.assertEqual(solutions,{p.id:tuple(p.solution) for p in level.puzzles.puzzles.values() if p.type=='sequence'})
            previous=solutions
        one=PuzzleLevel(seed=42);two=PuzzleLevel(seed=42)
        self.assertEqual(one.puzzles.snapshot(),two.puzzles.snapshot())

    def test_feedback_freeze_reset_and_full_chest_render(self):
        pygame.init()
        try:
            window=pygame.display.set_mode((940,724));canvas=pygame.Surface(SIZE)
            game=PuzzleGame();level=game.level
            initial={p.id:tuple(p.solution) for p in level.puzzles.puzzles.values() if p.type=='sequence'}
            level.notify('solved','Test de la sequence',puzzle_id='statues_blue')
            before=level.time
            game.update(.03,(0,0))
            self.assertEqual(level.time,before)
            self.assertGreater(game.feedback_fx.freeze_remaining,0)
            game.event(pygame.K_m)
            age=game.feedback_fx.pulses[0].age
            game.update(2,(0,0))
            self.assertEqual(game.feedback_fx.pulses[0].age,age)
            game.event(pygame.K_m)
            game.update(.1,(0,0))
            self.assertGreater(level.time,before)
            self.assertLess(level.time-before,.1)
            self.solve(level,'statues_blue')
            for _ in range(40):
                game.update(.05,(0,0))
                game.draw(canvas);game.present(canvas,window)
            game.event(pygame.K_r)
            self.assertEqual((game.level.mode.poison_potions.count,game.level.mode.resurrection_potions.count),(3,3))
            for pid,old in initial.items():self.assertNotEqual(old,tuple(game.level.puzzles.puzzles[pid].solution))
        finally:pygame.quit()

    def test_random_paths_are_valid_and_stable(self):
        paths=set()
        for seed in range(50):
            level=PuzzleLevel(seed=seed)
            cells=level.objects_path
            self.assertEqual(cells[0],(37,34))
            self.assertEqual(cells[-1],(39,38))
            self.assertEqual(len(cells),len(set(cells)))
            self.assertLessEqual(len(cells),19)
            for a,b in zip(cells,cells[1:]):self.assertEqual(abs(a[0]-b[0])+abs(a[1]-b[1]),1)
            for cell in cells:self.assertTrue(level.passable(*cell))
            original=list(cells)
            level.reset_path()
            self.assertEqual(level.objects_path,original)
            paths.add(tuple(cells))
        self.assertGreater(len(paths),10)

    def test_render_and_pause(self):
        pygame.init()
        try:
            window=pygame.display.set_mode((940,724));canvas=pygame.Surface(SIZE)
            game=PuzzleGame();game.event(pygame.K_p);game.event(pygame.K_m)
            game.update(3,(0,0));self.assertEqual(game.level.mode.time_remaining,10)
            game.draw(canvas);game.present(canvas,window)
            game.event(pygame.K_m);game.draw(canvas);game.present(canvas,window)
        finally:pygame.quit()
