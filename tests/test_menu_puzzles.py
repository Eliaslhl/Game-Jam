"""Regression du rebase : Jouer doit lancer les enigmes, sans fermer Pygame."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
import pygame
from settings import SCREEN_WIDTH,SCREEN_HEIGHT
from systems.ghost_mode import GhostModeController,PlayerState
from systems.puzzle_level import PuzzleLevel
from views import menu_view,puzzle_view


class MenuPuzzleIntegrationTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
        pygame.event.clear()

    def tearDown(self):
        pygame.quit()

    def test_play_starts_puzzles_and_restores_menu(self):
        original=puzzle_view.PuzzleGame
        games=[]
        def make_game():
            game=original()
            games.append(game)
            return game
        def choose_play(scene,event):
            return 'play' if event.type==pygame.USEREVENT else None
        pygame.event.post(pygame.event.Event(pygame.USEREVENT))
        with patch('sys.argv',['main.py','--smoke-test']), \
             patch.object(menu_view.MenuScene,'handle_event',choose_play), \
             patch.object(menu_view,'_fullscreen_window',lambda:pygame.display.set_mode((940,724))), \
             patch.object(puzzle_view,'PuzzleGame',side_effect=make_game):
            menu_view.run(self.screen)
        self.assertEqual(len(games),1)
        self.assertIsInstance(games[0].level,PuzzleLevel)
        self.assertEqual(len(games[0].level.puzzles.puzzles),3)
        self.assertEqual(games[0].level.mode.resurrection_potions.count,3)
        self.assertTrue(pygame.get_init())
        # Le menu conserve le plein ecran courant, fourni ici par le mock.
        self.assertEqual(pygame.display.get_surface().get_size(),(940,724))

    def test_escape_returns_to_menu_without_quitting_pygame(self):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertEqual(puzzle_view.run(self.screen),'menu')
        self.assertTrue(pygame.get_init())

    def test_tutorial_timeout_policy_is_preserved(self):
        mode=GhostModeController()
        mode.enter_ghost_mode((0,0))
        mode.update(11)
        self.assertEqual(mode.state,PlayerState.DEAD)
        level=PuzzleLevel()
        level.action(pygame.K_p)
        level.update(11)
        self.assertEqual(level.mode.state,PlayerState.ALIVE)
        self.assertEqual(level.mode.resurrection_potions.count,3)
