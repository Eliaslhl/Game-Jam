"""Adaptive sanctuary score, isolated from the menu's streaming music."""
from pathlib import Path
import random
import pygame

ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'sounds' / 'sanctuary'


class SanctuaryAudio:
    def __init__(self):
        self.enabled = bool(pygame.mixer.get_init())
        self.sounds = {}
        self.room = None
        self.active_bed = 0
        self.gains = [0., 0.]
        self.clock = self.duck_until = self.next_beat = self.next_step = 0.
        self.last = {}
        self.sequence = 0
        self.rng = random.Random()
        self.next_haunt = 0.
        self.paused = False
        self.stopped = False
        if not self.enabled:
            return
        pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
        pygame.mixer.set_reserved(8)
        self.channels = [pygame.mixer.Channel(i) for i in range(8)]
        for path in ASSETS.glob('*.wav'):
            try:
                self.sounds[path.stem] = pygame.mixer.Sound(str(path))
            except pygame.error:
                pass
        if 'amb_spectral' in self.sounds:
            self.channels[2].play(self.sounds['amb_spectral'], loops=-1)
            self.channels[2].set_volume(0)

    def play(self, name, volume=.65, pan=0., channel=None):
        if not self.enabled or self.stopped or self.paused or name not in self.sounds:
            return
        if channel is None:
            channel = next((c for c in self.channels[5:7] if not c.get_busy()), self.channels[6])
        channel.set_volume(volume*(1-max(0,pan)*.5), volume*(1+min(0,pan)*.5))
        channel.play(self.sounds[name])

    def emit(self, event, listener):
        kind = event['kind']
        if self.clock-self.last.get(kind, -100) < (.25 if kind == 'wrong' else .10):
            return
        self.last[kind] = self.clock
        name = kind
        if kind == 'correct':
            pid=event.get('puzzle_id')
            name = ('stone' if pid=='wall' else 'stone_slide' if pid=='statue' else
                    ('path_' if pid=='path_sp' else 'correct_')+str(min(4,self.sequence)))
            self.sequence += 1
        if kind in ('wrong', 'solved'):
            self.sequence = 0
        if kind == 'solved':
            self.duck_until = self.clock+2.4
            if self.enabled:
                self.channels[7].fadeout(180)
        pan = max(-1., min(1., (event['position'][0]-listener[0])/180))
        self.play(name, .64 if kind == 'solved' else .48, pan,
                  channel=self.channels[4] if kind == 'solved' and self.enabled else None)

    def set_paused(self, paused):
        if not self.enabled or paused == self.paused:
            return
        self.paused = paused
        for channel in self.channels:
            channel.pause() if paused else channel.unpause()

    def update(self, dt, level, moving=False, paused=False):
        if not self.enabled or self.stopped:
            return
        if level.won or level.lost:
            self.stop()
            return
        self.set_paused(paused)
        if paused:
            return
        self.clock += dt
        room = level.trial_room
        if level.special_room is not None:
            # Geography determines atmosphere, so music cannot reveal gold.
            room = level.special_room
        if room != self.room:
            self.room = room
            self.sequence = 0
            self.active_bed = 1-self.active_bed
            channel = self.channels[self.active_bed]
            channel.stop()
            self.gains[self.active_bed] = 0
            sound_room = {'NW':'statues_sp', 'NE':'path_sp', 'W':'gold'}.get(room, room)
            sound = self.sounds.get('amb_'+str(sound_room))
            if sound:
                channel.set_volume(0)
                channel.play(sound, loops=-1)
                self.play('enter', .38)
            self.next_haunt = self.clock+2.8
            self.channels[7].fadeout(450)
        # Smooth gain interpolation keeps both sides of a room transition audible.
        duck = .38 if self.clock < self.duck_until else 1.
        for i in range(2):
            target = .30*duck if room and i == self.active_bed else 0.
            self.gains[i] += (target-self.gains[i])*min(1,dt*2.5)
            self.channels[i].set_volume(self.gains[i])
        self.channels[2].set_volume(.13*duck if level.ghost else 0)
        if room and self.clock >= self.next_haunt and self.clock >= self.duck_until:
            name = {'tomb':'whisper', 'statue':'roots', 'wall':'chains',
                    'NW':'wood', 'NE':'ice', 'W':'drip'}[room]
            self.play('haunt_'+name, .26, self.rng.uniform(-.85,.85), self.channels[7])
            self.next_haunt = self.clock+self.rng.uniform(7,12)
        if level.ghost and level.mode.time_remaining < 8 and self.clock >= self.next_beat:
            danger = 1-max(0, level.mode.time_remaining)/8
            self.play('heartbeat', .18+.17*danger, channel=self.channels[3])
            self.next_beat = self.clock+1.0-.55*danger
        elif not level.ghost:
            self.channels[3].stop()
        if moving and not level.ghost and self.clock >= self.next_step:
            self.play('step', .13)
            self.next_step = self.clock+.34

    def stop(self):
        if self.enabled:
            for channel in self.channels:
                channel.stop()
        self.stopped = True
