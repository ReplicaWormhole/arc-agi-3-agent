import sys
import unittest
from pathlib import Path

import numpy as np
from arcengine import FrameDataRaw, GameAction

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))

from arc_agent.explorer import ExplorationController, TransitionGraph, state_key


def frame(
    values: list[list[int]], *, levels: int = 0, actions: list[int] | None = None
) -> FrameDataRaw:
    result = FrameDataRaw(
        levels_completed=levels,
        win_levels=3,
        available_actions=actions or [1, 2],
    )
    result.frame = [np.array(values, dtype=np.int8)]
    return result


class ExplorerTests(unittest.TestCase):
    def test_explorer_does_not_repeat_an_exact_state_action_pair(self) -> None:
        controller = ExplorationController()
        initial = frame([[0]], actions=[1, 2])
        self.assertEqual(controller.select_exploration_action(initial), GameAction.ACTION1)
        controller.observe(initial, GameAction.ACTION1, frame([[1]], actions=[1, 2]))
        self.assertEqual(controller.select_exploration_action(initial), GameAction.ACTION2)

    def test_explorer_balances_actions_across_new_states(self) -> None:
        controller = ExplorationController()
        initial = frame([[0]], actions=[1, 2])
        next_state = frame([[1]], actions=[1, 2])
        controller.observe(initial, GameAction.ACTION1, next_state)
        self.assertEqual(controller.select_exploration_action(next_state), GameAction.ACTION2)

    def test_action_hypothesis_is_accepted_only_after_two_consistent_observations(self) -> None:
        controller = ExplorationController()
        first = frame([[0]])
        second = frame([[1]])
        third = frame([[2]])
        controller.observe(first, GameAction.ACTION1, second)
        once = controller.report(second)["action_hypotheses"][0]
        self.assertFalse(once["accepted"])
        controller.observe(second, GameAction.ACTION1, third)
        twice = controller.report(third)["action_hypotheses"][0]
        self.assertTrue(twice["accepted"])
        self.assertEqual(twice["claim"], "changes the rendered state")

    def test_conflicting_observation_rejects_action_claim(self) -> None:
        controller = ExplorationController()
        first = frame([[0]])
        changed = frame([[1]])
        unchanged = frame([[1]])
        controller.observe(first, GameAction.ACTION1, changed)
        controller.observe(changed, GameAction.ACTION1, unchanged)
        hypothesis = controller.report(unchanged)["action_hypotheses"][0]
        self.assertFalse(hypothesis["accepted"])
        self.assertEqual(hypothesis["contradictions"], 1)

    def test_graph_planner_finds_observed_progress_route(self) -> None:
        initial = frame([[0]], actions=[1])
        middle = frame([[1]], actions=[2])
        goal = frame([[2]], levels=1, actions=[1])
        graph = TransitionGraph()
        graph.record(initial, GameAction.ACTION1, middle)
        graph.record(middle, GameAction.ACTION2, goal)
        self.assertEqual(graph.shortest_plan_to_progress(initial), [1, 2])
        self.assertEqual(state_key(initial), state_key(frame([[0]], actions=[1])))
        self.assertNotEqual(state_key(initial), state_key(frame([[0]], levels=1, actions=[1])))
