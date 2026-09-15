"""IA de patrouille simple (aller-retour / suivi de chemin)."""
from src.game.enemies.base_enemy import BaseEnemy


class PatrolEnemy(BaseEnemy):
    def __init__(self, path_points: list[tuple[float, float]]) -> None:
        super().__init__()
        self.path_points = path_points
        self.current_target_index = 0

    def update(self, delta_time: float = 1 / 60) -> None:
        pass
