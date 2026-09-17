"""Exercise the real mixer with a dummy output device."""
import os
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
from types import SimpleNamespace
import unittest
import pygame
from systems.audio_manager import SanctuaryAudio


class SanctuaryAudioTests(unittest.TestCase):
    def setUp(self):
        pygame.mixer.init()
        self.audio = SanctuaryAudio()
        self.level = SimpleNamespace(trial_room='tomb', special_room=None,
                                     special_content={'NW': 'path'}, ghost=False,
                                     won=False, lost=False,
                                     mode=SimpleNamespace(time_remaining=4))

    def tearDown(self):
        self.audio.stop()
        pygame.mixer.quit()

    def test_all_assets_and_room_transitions(self):
        self.assertEqual(len(self.audio.sounds), 36)
        self.audio.update(.1, self.level)
        previous = self.audio.active_bed
        self.assertTrue(self.audio.channels[previous].get_busy())
        self.level.trial_room = None
        self.level.special_room = 'NW'
        self.audio.update(.1, self.level)
        self.assertEqual(self.audio.room, 'NW')
        self.assertNotEqual(previous, self.audio.active_bed)
        self.assertTrue(self.audio.channels[previous].get_busy())
        self.assertTrue(self.audio.channels[self.audio.active_bed].get_busy())

    def test_pause_urgency_and_cleanup(self):
        self.level.ghost = True
        self.audio.update(.1, self.level)
        self.assertTrue(self.audio.channels[3].get_busy())
        clock = self.audio.clock
        self.audio.update(.5, self.level, paused=True)
        self.assertEqual(self.audio.clock, clock)
        self.audio.update(.1, self.level)
        self.assertFalse(self.audio.paused)
        self.level.won = True
        self.audio.update(.1, self.level)
        self.assertTrue(all(not c.get_busy() for c in self.audio.channels))

    def test_reward_ducks_ambience_and_spam_is_limited(self):
        event = dict(kind='solved', position=(0,0), puzzle_id='tomb')
        self.audio.emit(event, (0,0))
        self.assertGreater(self.audio.duck_until, self.audio.clock)
        self.audio.emit(event, (0,0))
        self.assertEqual(sum(c.get_busy() for c in self.audio.channels[4:]), 1)

    def test_no_audio_device_is_supported(self):
        self.audio.stop()
        pygame.mixer.quit()
        self.audio = SanctuaryAudio()
        self.audio.update(.1, self.level)
        self.audio.emit(dict(kind='door', position=(0,0)), (0,0))
        self.assertFalse(self.audio.enabled)
