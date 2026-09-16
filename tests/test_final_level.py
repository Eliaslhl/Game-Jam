"""Parcours reel du niveau : collisions, temps fantome, sceaux, cles et sortie."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import deque
import unittest
import pygame
from systems.final_level import FinalLevel
from views.final_map_view import FinalGame, SIZE


def route(level,start,goal,ghost=False):
    queue=deque([start]); parents={start:None}
    while queue:
        cell=queue.popleft()
        if cell==goal:
            path=[]
            while parents[cell] is not None:
                path.append(cell); cell=parents[cell]
            return path[::-1]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nxt=(cell[0]+dx,cell[1]+dy)
            if nxt not in parents and level.passable(*nxt,ghost=ghost) and (ghost or level.tile(*nxt)!='^'):
                parents[nxt]=cell; queue.append(nxt)
    return None


def follow(level,path):
    if path is None: raise AssertionError('Aucun chemin trouve')
    for cell in path:
        destination=level.center(cell)
        direction=destination-level.position
        speed=78 if level.ghost else 65
        level.update(direction.length()/speed,direction)
        if level.position.distance_to(destination)>.1:
            raise AssertionError(f'Collision inattendue vers {cell} : {level.position}')


class FinalLevelTests(unittest.TestCase):
    def test_three_seals_keys_and_exit_without_reset(self):
        level=FinalLevel()
        self.assertEqual(len(level.cells('123')),3)
        self.assertGreater(len(level.cells('Y')),level.mode.potions.count)
        for seal,door,key in zip('abc','ABC','123'):
            target=level.cells(seal)[0]
            # Choisir un point de depart vivant juste devant un passage spectral.
            candidates=[]
            for yellow in level.cells('Y'):
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    start=(yellow[0]+dx,yellow[1]+dy)
                    if not level.passable(*start,ghost=False): continue
                    alive_path=route(level,level.cell,start)
                    ghost_path=route(level,start,target,True)
                    if alive_path is not None and ghost_path is not None:
                        candidates.append((len(ghost_path),len(alive_path),alive_path,ghost_path))
            self.assertTrue(candidates,seal)
            _,_,alive_path,ghost_path=min(candidates,key=lambda c:(c[0],c[1]))
            follow(level,alive_path)
            body=level.position.copy()
            level.action(pygame.K_p)
            self.assertTrue(level.ghost)
            follow(level,ghost_path)
            self.assertIn(seal,level.seals)
            self.assertTrue(level.ghost,'Le sceau doit etre atteignable avant expiration')
            level.action(pygame.K_RETURN)
            self.assertEqual(level.position,body)
            gate=level.cells(door)[0]
            approaches=[]
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                path=route(level,level.cell,(gate[0]+dx,gate[1]+dy))
                if path is not None: approaches.append(path)
            self.assertTrue(approaches,door)
            follow(level,min(approaches,key=len))
            level.action(pygame.K_e)
            self.assertIn(door,level.doors)
            follow(level,route(level,level.cell,level.cells(key)[0]))
            self.assertIn(key,level.keys)
        follow(level,route(level,level.cell,level.cells('E')[0]))
        self.assertTrue(level.won)
        self.assertEqual(level.deaths,0)

    def test_fog_restrictions_and_safe_return(self):
        level=FinalLevel()
        fog=level.cells('~')[0]
        self.assertFalse(level.passable(*fog))
        level.action(pygame.K_p)
        self.assertTrue(level.passable(*fog))
        self.assertEqual(level.vision,142)
        level.position.update(level.center(fog))
        level.update(11)
        self.assertFalse(level.ghost)
        self.assertFalse(level.blocked(level.position))
        self.assertEqual(level.vision,94)
        level.position.update(level.center(level.cells('1')[0]))
        level.action(pygame.K_p)
        level.update(0)
        self.assertFalse(level.keys)
        level.action(pygame.K_e)
        self.assertFalse(level.doors)

    def test_potions_do_not_respawn_after_trap(self):
        level=FinalLevel()
        cell=level.cells('P')[0]
        level.position.update(level.center(cell)); level.update(0)
        self.assertEqual(level.mode.potions.count,4)
        level.position.update(level.center(level.cells('^')[0])); level.update(0)
        self.assertEqual(level.deaths,1)
        level.position.update(level.center(cell)); level.update(0)
        self.assertEqual(level.mode.potions.count,4)

    def test_render_and_paused_timer(self):
        pygame.init()
        try:
            pygame.display.set_mode(SIZE)
            game=FinalGame(); canvas=pygame.Surface(SIZE)
            game.event(pygame.K_p)
            game.event(pygame.K_m)
            game.update(2,(1,0))
            self.assertEqual(game.level.mode.time_remaining,10)
            game.draw(canvas)
            game.event(pygame.K_m); game.event(pygame.K_h); game.draw(canvas)
            game.event(pygame.K_h)
            game.level.position.update(game.level.center((7,30)))
            game.update_camera(); game.draw(canvas)
        finally:
            pygame.quit()
