"""Verification des regles fantome et du parcours Pygame de Kadir."""
import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from systems.ghost_mode import GhostModeController, PlayerState
from systems.interactions import can_interact, is_visible
from test_map.map_test_kadir import TestMapKadir, PLAN


class GhostTests(unittest.TestCase):
    def test_potions_timer_and_return(self):
        mode = GhostModeController()
        for _ in range(3):
            self.assertTrue(mode.enter_ghost_mode((100, 100)))
            count = mode.potions.count
            self.assertFalse(mode.enter_ghost_mode((200, 200)))
            self.assertEqual(mode.potions.count, count)
            self.assertFalse(can_interact(mode.state, 'key'))
            self.assertTrue(is_visible(mode.state, True))
            self.assertTrue(mode.can_pass_wall(True))
            self.assertFalse(mode.can_pass_wall(False))
            self.assertIsNone(mode.update(9))
            self.assertEqual(mode.update(2), (100, 100))
            self.assertEqual(mode.state, PlayerState.ALIVE)
            self.assertFalse(is_visible(mode.state, True))
        self.assertFalse(mode.enter_ghost_mode())

    def test_map_collisions_interactions_and_completion(self):
        pygame.init()
        try:
            screen = pygame.display.set_mode((800, 935))
            game = TestMapKadir()
            self.assertTrue(all(len(row) == 20 for row in PLAN))
            self.assertEqual(len(game.animation.frames), 5)
            yellow = pygame.Rect(250, 90, 22, 22)
            self.assertTrue(game.blocked(yellow))
            game.action(pygame.K_p)
            self.assertFalse(game.blocked(yellow))
            self.assertTrue(game.blocked(pygame.Rect(250, 130, 22, 22)))
            game.position.update(340, 180)
            game.update(0, pygame.Vector2())
            self.assertFalse(game.key_collected)
            game.position.update(140, 660)
            game.action(pygame.K_e)
            self.assertFalse(game.door_open)
            game.draw(screen, 0.2, True)
            game.update(11, pygame.Vector2())
            self.assertEqual(game.position, (100, 100))
            game.move(pygame.Vector2(0, 1), 560 / 180)
            game.move(pygame.Vector2(1, 0), 40 / 180)
            game.action(pygame.K_e)
            self.assertTrue(game.door_open)
            game.move(pygame.Vector2(1, 0), 200 / 180)
            game.move(pygame.Vector2(0, -1), 480 / 180)
            game.update(0, pygame.Vector2())
            self.assertTrue(game.key_collected)
            game.move(pygame.Vector2(0, 1), 480 / 180)
            game.move(pygame.Vector2(1, 0), 320 / 180)
            game.update(0, pygame.Vector2())
            self.assertTrue(game.won)
            game.draw(screen, 0.1, False)
        finally:
            pygame.quit()

