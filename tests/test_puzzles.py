"""Parcours reels des salles, verrouillage et rendu des nouvelles epreuves."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import deque
import unittest
from unittest.mock import patch
import pygame
from systems.puzzle_level import PuzzleLevel
from views.puzzle_view import PuzzleGame, SIZE


def reachable(level, ghost=None):
    pending=deque([level.cell]); parents={level.cell:None}
    while pending:
        x,y=pending.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            cell=(x+dx,y+dy)
            if cell not in parents and level.passable(*cell,ghost=ghost) and cell not in level.holes:
                parents[cell]=(x,y);pending.append(cell)
    return parents


def walk(level,target):
    parents=reachable(level)
    if target not in parents: raise AssertionError(f'Inaccessible: {level.cell} -> {target}')
    path=[];cell=target
    while parents[cell] is not None:
        path.append(cell);cell=parents[cell]
    for cell in reversed(path):
        delta=level.center(cell)-level.position
        level.update(delta.length()/(78 if level.ghost else 65),delta)
        if level.position.distance_to(level.center(cell))>.01:
            raise AssertionError(f'Collision vers {cell}: {level.cell}')


class PuzzleTests(unittest.TestCase):
    def solve(self,level,pid):
        if pid=='tomb':
            walk(level,(10+level.targets['tomb'],36));level.action(pygame.K_e)
        elif pid=='wall':
            walk(level,(40+level.targets['wall'],24))
            for _ in range(3):level.action(pygame.K_e)
        else:
            tx,ty=level.targets['statue']
            if tx!=37:
                walk(level,(36 if tx>37 else 38,37));level.action(pygame.K_e)
            for y in (38,37):
                walk(level,(tx,y));level.action(pygame.K_e)
        self.assertTrue(level.puzzles.puzzles[pid].solved)
        chest=next(o for o in level.objects if o.id==pid+'_chest')
        walk(level,chest.cell);level.action(pygame.K_e);level.update(.7)
        self.assertEqual(chest.state,'open')
        self.assertIn(level.puzzles.puzzles[pid].reward['id'],level.keys)
        before=level.mode.poison_potions.count
        self.assertEqual(chest.interact(level),'locked')
        self.assertEqual(level.mode.poison_potions.count,before)

    def test_random_chains_and_no_ghost_bypass(self):
        orders=set();colors=set()
        for seed in range(30):
            level=PuzzleLevel(seed=seed);orders.add(tuple(level.order))
            doors=[o for o in level.objects if o.id.startswith('entry_')]
            self.assertEqual(sum(o.state=='open' for o in doors),1)
            for index,pid in enumerate(level.order):
                for ghost in (False,True):
                    cells=reachable(level,ghost)
                    for locked in level.order[index+1:]:
                        self.assertFalse(any(level.rooms[locked].collidepoint(c) for c in cells))
                self.solve(level,pid)
                if index<2:
                    next_pid=level.order[index+1]
                    door=next(o for o in doors if o.id=='entry_'+next_pid)
                    colors.update(door.required_keys)
                    x,y=door.cell
                    walk(level,(x-1,y) if next_pid=='wall' else (x,y-1))
                    level.action(pygame.K_e)
                    self.assertEqual(door.state,'open')
            self.assertIn('silver',level.keys)
            self.assertEqual(len(level.keys),3)
            self.assertEqual(len(level.puzzles.rewards),3)
            self.assertFalse(level.won)
        self.assertEqual(len(orders),6)
        self.assertEqual(colors,{'blue','red','green'})

    def test_ghost_cannot_manipulate_or_loot(self):
        level=PuzzleLevel(seed=2);level.action(pygame.K_p)
        for obj in level.objects:
            self.assertEqual(obj.interact(level),'blocked')
        self.assertFalse(level.keys)
        self.assertFalse(any(p.solved for p in level.puzzles.puzzles.values()))

    def test_wrong_targets_and_resurrection_on_decor(self):
        level=PuzzleLevel(seed=2)
        wrong=next(o for o in level.objects if o.type=='tomb' and o.id!='tomb_'+str(level.targets['tomb']))
        self.assertEqual(wrong.interact(level),'wrong')
        self.assertFalse(level.puzzles.puzzles['tomb'].solved)
        wall=next(o for o in level.objects if o.type=='wall' and o.id!='wall_'+str(level.targets['wall']))
        self.assertEqual(wall.interact(level),'wrong');self.assertEqual(level.wall_hits,0)
        level.action(pygame.K_p);level.position.update(level.center(wrong.cell))
        level.action(pygame.K_RETURN)
        self.assertFalse(level.ghost);self.assertFalse(level.blocked(level.position))

    def test_render_effects_map_music_and_restart(self):
        pygame.init()
        try:
            window=pygame.display.set_mode((940,724));canvas=pygame.Surface(SIZE)
            game=PuzzleGame();level=game.level
            with patch('pygame.mixer.music.pause') as pause, patch('pygame.mixer.music.unpause') as resume:
                for pid in level.order:
                    level.position.update(level.center(level.rooms[pid].center))
                    game.update(.01,(0,0))
                    level.notify('solved','Test',puzzle_id=pid)
                    for _ in range(5):
                        game.update(.1,(0,0));game.draw(canvas);game.present(canvas,window)
                    level.position.update(level.center(level.spawn));game.update(.1,(0,0))
                self.assertEqual(pause.call_count,3);self.assertEqual(resume.call_count,3)
            game.event(pygame.K_p);game.draw(canvas)
            game.event(pygame.K_m);before=level.time
            game.update(3,(0,0));self.assertEqual(level.time,before)
            game.draw(canvas);game.present(canvas,window)
            game.event(pygame.K_r)
            self.assertFalse(game.level.keys)
        finally:pygame.quit()


if __name__=='__main__':unittest.main()
