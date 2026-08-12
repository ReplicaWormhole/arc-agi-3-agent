"""Small deterministic baselines used to validate the experiment harness."""

from __future__ import annotations

import random
from typing import Protocol, Sequence

from arcengine import GameAction


class Policy(Protocol):
    """Select one legal action from a frame's advertised action identifiers."""

    def select(self, available_actions: Sequence[int]) -> GameAction: ...


def _legal_actions(available_actions: Sequence[int]) -> list[GameAction]:
    # The ARC engine's enum constructor is not stable across toolkit releases:
    # in the installed release it retains tuple member definitions even though
    # ``action.value`` is an integer.  ``from_id`` is its supported conversion.
    actions = [GameAction.from_id(action_id) for action_id in available_actions]
    if not actions:
        raise ValueError("environment exposed no legal actions")
    return actions


class CyclicPolicy:
    """Choose legal actions in their advertised order, cycling between calls."""

    def __init__(self) -> None:
        self._index = 0

    def select(self, available_actions: Sequence[int]) -> GameAction:
        actions = _legal_actions(available_actions)
        action = actions[self._index % len(actions)]
        self._index += 1
        return action


class RandomPolicy:
    """Choose legal actions with a private seeded pseudo-random generator."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def select(self, available_actions: Sequence[int]) -> GameAction:
        return self._rng.choice(_legal_actions(available_actions))
