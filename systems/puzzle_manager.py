"""Sequences, observation spectrale et recompenses independantes du rendu."""
from dataclasses import dataclass, field
from itertools import permutations
import random


@dataclass
class Puzzle:
    id: str
    type: str
    solution: list[str]
    reward: dict
    required_clues: set[str] = field(default_factory=set)
    observed: set[str] = field(default_factory=set)
    current_sequence: list[str] = field(default_factory=list)
    solved: bool = False


class PuzzleManager:
    # Une nouvelle partie dans la meme session ne reprend jamais le meme code.
    _previous_solutions = {}

    def __init__(self, definitions, seed=None):
        rng = random.Random(seed) if seed is not None else random.SystemRandom()
        self.puzzles = {}
        for definition in definitions:
            if definition['type'] == 'sequence':
                members = definition['members']
                choices = list(permutations(members))
                previous = self._previous_solutions.get(definition['id'])
                if seed is None and previous in choices and len(choices) > 1:
                    choices.remove(previous)
                solution = list(rng.choice(choices))
                if seed is None:
                    self._previous_solutions[definition['id']] = tuple(solution)
            else:
                solution = list(definition['solution'])
            self.puzzles[definition['id']] = Puzzle(
                definition['id'], definition['type'], solution, definition['reward'],
                set(definition.get('required_clues', [])))
        self.rewards = []

    def observe(self, puzzle_id, clue_id, ghost):
        if ghost:
            puzzle = self.puzzles[puzzle_id]
            if clue_id not in puzzle.observed:
                puzzle.observed.add(clue_id)
                return True
        return False

    def submit(self, puzzle_id, object_id, ghost=False):
        puzzle = self.puzzles[puzzle_id]
        if ghost:
            return 'blocked'
        if puzzle.solved:
            return 'already_solved'
        if not puzzle.required_clues <= puzzle.observed:
            return 'unobserved'
        expected = puzzle.solution[len(puzzle.current_sequence)]
        if object_id != expected:
            self.reset(puzzle_id)
            return 'wrong'
        puzzle.current_sequence.append(object_id)
        if puzzle.current_sequence == puzzle.solution:
            puzzle.solved = True
            self.rewards.append(dict(puzzle.reward))
            return 'solved'
        return 'correct'

    def reset(self, puzzle_id):
        puzzle = self.puzzles[puzzle_id]
        if not puzzle.solved:
            puzzle.current_sequence.clear()

    def snapshot(self):
        return {p.id: {'solution': list(p.solution), 'solved': p.solved, 'observed': sorted(p.observed), 'current_sequence': list(p.current_sequence)} for p in self.puzzles.values()}
