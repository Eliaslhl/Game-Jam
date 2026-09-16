
import random


class GhostHazards:
    def __init__(self, eligible_cells, count=2, rng=None):
        rng = rng or random
        cells = list(eligible_cells)
        picked = rng.sample(cells, min(count, len(cells))) if cells else []
        self.cells = frozenset(picked)

    def is_lethal(self, cell) -> bool:
        return cell in self.cells

    def __contains__(self, cell) -> bool:
        return cell in self.cells

    def __iter__(self):
        return iter(self.cells)

    def __bool__(self) -> bool:
        return bool(self.cells)

    def __len__(self) -> int:
        return len(self.cells)
