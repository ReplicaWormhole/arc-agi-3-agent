"""On-policy exploration, falsifiable hypotheses, and empirical planning.

This module deliberately never forks, resets, or clones a live game to test a
counterfactual action.  A transition becomes evidence only after the executor
has actually observed it.  Local development may run many independent
episodes, but a competition playthrough must use one `ExplorationController`.
"""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from arcengine import FrameDataRaw, GameAction


def action_from_id(action_id: int) -> GameAction:
    """Convert an environment-advertised integer using the SDK-supported API."""
    return GameAction.from_id(action_id)


def state_key(frame: FrameDataRaw) -> str:
    """Return an exact, renderer-independent key for a visible game state."""
    digest = hashlib.sha256()
    digest.update(frame.game_id.encode())
    digest.update(frame.levels_completed.to_bytes(4, byteorder="big", signed=False))
    for plane in frame.frame:
        digest.update(str(plane.dtype).encode())
        digest.update(np.asarray(plane.shape, dtype=np.int64).tobytes())
        digest.update(plane.tobytes())
    digest.update(bytes(frame.available_actions))
    return digest.hexdigest()


def changed_cells(before: FrameDataRaw, after: FrameDataRaw) -> int:
    """Count changed pixels across corresponding rendered planes."""
    if len(before.frame) != len(after.frame):
        return -1
    differences = 0
    for old, new in zip(before.frame, after.frame, strict=True):
        if old.shape != new.shape:
            return -1
        differences += int(np.count_nonzero(old != new))
    return differences


@dataclass(frozen=True)
class Transition:
    source: str
    action_id: int
    target: str
    changed_cells: int
    levels_before: int
    levels_after: int

    @property
    def progressed(self) -> bool:
        return self.levels_after > self.levels_before


@dataclass(frozen=True)
class ActionHypothesis:
    """A deliberately modest, directly testable claim about one legal action."""

    action_id: int
    claim: str
    confirmations: int
    contradictions: int

    @property
    def confidence(self) -> float:
        total = self.confirmations + self.contradictions
        return self.confirmations / total if total else 0.0

    @property
    def accepted(self) -> bool:
        return self.confirmations >= 2 and self.contradictions == 0


class TransitionGraph:
    """Exact observed state-action graph; it contains no imagined transitions."""

    def __init__(self) -> None:
        self._transitions: dict[tuple[str, int], Transition] = {}

    def record(self, before: FrameDataRaw, action: GameAction, after: FrameDataRaw) -> Transition:
        transition = Transition(
            source=state_key(before),
            action_id=action.value,
            target=state_key(after),
            changed_cells=changed_cells(before, after),
            levels_before=before.levels_completed,
            levels_after=after.levels_completed,
        )
        existing = self._transitions.get((transition.source, transition.action_id))
        if existing is not None and existing != transition:
            raise ValueError("same state-action pair produced inconsistent outcomes")
        self._transitions[(transition.source, transition.action_id)] = transition
        return transition

    def contains(self, frame: FrameDataRaw, action_id: int) -> bool:
        return (state_key(frame), action_id) in self._transitions

    def transitions_from(self, frame: FrameDataRaw) -> list[Transition]:
        source = state_key(frame)
        return [edge for (origin, _), edge in self._transitions.items() if origin == source]

    def predict(self, frame: FrameDataRaw, action_id: int) -> Transition | None:
        return self._transitions.get((state_key(frame), action_id))

    def action_observation_count(self, action_id: int) -> int:
        """Return how often an action has been observed across the trajectory."""
        return sum(edge.action_id == action_id for edge in self._transitions.values())

    def shortest_plan_to_progress(self, frame: FrameDataRaw) -> list[int] | None:
        """Find a plan to an *already observed* progress transition, if one exists."""
        start = state_key(frame)
        queue: deque[tuple[str, list[int]]] = deque([(start, [])])
        visited = {start}
        while queue:
            node, path = queue.popleft()
            for (source, action_id), edge in self._transitions.items():
                if source != node:
                    continue
                candidate = [*path, action_id]
                if edge.progressed:
                    return candidate
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append((edge.target, candidate))
        return None


class HypothesisLedger:
    """Tracks action-effect claims and rejects claims on contrary observations."""

    def __init__(self) -> None:
        self._outcomes: dict[int, list[bool]] = {}

    def observe(self, transition: Transition) -> None:
        self._outcomes.setdefault(transition.action_id, []).append(transition.changed_cells != 0)

    def hypotheses(self, legal_actions: Sequence[int]) -> list[ActionHypothesis]:
        result: list[ActionHypothesis] = []
        for action_id in legal_actions:
            outcomes = self._outcomes.get(action_id, [])
            changed = sum(outcomes)
            unchanged = len(outcomes) - changed
            if not outcomes:
                claim = "untested"
                confirmations = contradictions = 0
            elif changed >= unchanged:
                claim = "changes the rendered state"
                confirmations, contradictions = changed, unchanged
            else:
                claim = "leaves the rendered state unchanged"
                confirmations, contradictions = unchanged, changed
            result.append(ActionHypothesis(action_id, claim, confirmations, contradictions))
        return result

    def game_hypothesis(self, graph: TransitionGraph) -> str:
        if any(edge.progressed for edge in graph._transitions.values()):
            return "Increasing levels_completed is observed evidence of progress."
        return (
            "The completion objective is not yet identified; no observed action "
            "increased levels_completed."
        )


class ExplorationController:
    """Choose untried actions first, then switch only to verified graph planning."""

    def __init__(self) -> None:
        self.graph = TransitionGraph()
        self.ledger = HypothesisLedger()

    def select_exploration_action(self, frame: FrameDataRaw) -> GameAction | None:
        """Balance action coverage without repeating an exact state-action pair."""
        candidates = [
            action_id
            for action_id in frame.available_actions
            if not self.graph.contains(frame, action_id)
        ]
        if not candidates:
            return None
        selected = min(
            candidates,
            key=lambda action_id: self.graph.action_observation_count(action_id),
        )
        return action_from_id(selected)

    def observe(self, before: FrameDataRaw, action: GameAction, after: FrameDataRaw) -> Transition:
        transition = self.graph.record(before, action, after)
        self.ledger.observe(transition)
        return transition

    def planning_ready(self, frame: FrameDataRaw) -> bool:
        """Require a fully observed route to progress before exploiting the graph."""
        plan = self.graph.shortest_plan_to_progress(frame)
        return plan is not None and all(
            self.graph.predict(frame, action_id) is not None
            for action_id in frame.available_actions
        )

    def select_planned_action(self, frame: FrameDataRaw) -> GameAction | None:
        plan = self.graph.shortest_plan_to_progress(frame)
        return action_from_id(plan[0]) if plan else None

    def report(self, frame: FrameDataRaw) -> dict[str, object]:
        hypotheses = self.ledger.hypotheses(frame.available_actions)
        return {
            "game_hypothesis": self.ledger.game_hypothesis(self.graph),
            "action_hypotheses": [
                {
                    "action_id": item.action_id,
                    "claim": item.claim,
                    "confirmations": item.confirmations,
                    "contradictions": item.contradictions,
                    "confidence": item.confidence,
                    "accepted": item.accepted,
                }
                for item in hypotheses
            ],
            "planning_ready": self.planning_ready(frame),
        }
