"""Correspondance clefs <-> portes."""


class Door:
    def __init__(self, door_id: str, required_key_id: str) -> None:
        self.door_id = door_id
        self.required_key_id = required_key_id
        self.is_open = False

    def try_open(self, keys_held: list[str]) -> bool:
        if self.required_key_id in keys_held:
            self.is_open = True
        return self.is_open


class Key:
    def __init__(self, key_id: str) -> None:
        self.key_id = key_id
