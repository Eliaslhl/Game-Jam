"""Regles d'interaction selon l'etat du joueur (le fantome ne touche rien de physique).

Responsable : Kadir
"""


from systems.ghost_mode import PlayerState


def can_interact(player_state, target=None) -> bool:
    """Determine si l'entite courante peut interagir avec `target` (clef, levier...)."""
    return player_state is PlayerState.ALIVE


def is_visible(player_state, ghost_only: bool = False) -> bool:
    return not ghost_only or player_state is PlayerState.GHOST
