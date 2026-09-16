"""Interface commune aux objets d'enigme et a leur visibilite."""
from dataclasses import dataclass, field


@dataclass
class PuzzleObject:
    id: str
    type: str
    cell: tuple[int, int]
    puzzle_id: str | None = None
    state: str = 'idle'
    interaction_allowed: bool = True
    visible_state: str = 'both'
    required_keys: list[str] = field(default_factory=list)
    text: str = ''
    ghost_passable: bool = False
    key_id: str | None = None
    clue_target: str | None = None
    clue_index: int | None = None
    loot: dict = field(default_factory=dict)

    @classmethod
    def from_data(cls, data):
        return cls(**{**data, 'cell': tuple(data['cell'])})

    def visible_to(self, player):
        return self.visible_state == 'both' or self.visible_state == ('ghost' if player.ghost else 'alive')

    def interact(self, player):
        if player.ghost or not self.interaction_allowed or not self.visible_to(player):
            return 'blocked'
        return player.interact_object(self)
