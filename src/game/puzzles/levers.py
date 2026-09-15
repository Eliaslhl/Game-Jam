"""Leviers activables (etat vivant) qui ouvrent des portes ou declenchent des mecanismes."""


class Lever:
    def __init__(self, linked_door_id: str) -> None:
        self.linked_door_id = linked_door_id
        self.activated = False

    def activate(self) -> None:
        self.activated = True
