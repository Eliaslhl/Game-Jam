"""Indices, symboles et passages visibles uniquement en mode Fantome."""


class SecretClue:
    def __init__(self, position: tuple[float, float], text: str) -> None:
        self.position = position
        self.text = text
        self.visible_in_ghost_mode = True
