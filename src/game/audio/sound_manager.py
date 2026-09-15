"""Chargement et lecture des sons/musiques.

Responsable : Thomas
"""
import arcade


class SoundManager:
    def __init__(self) -> None:
        self._sounds: dict[str, arcade.Sound] = {}

    def load(self, name: str, path: str) -> None:
        self._sounds[name] = arcade.Sound(path)

    def play(self, name: str) -> None:
        if name in self._sounds:
            arcade.play_sound(self._sounds[name])
