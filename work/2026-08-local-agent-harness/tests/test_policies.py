import sys
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))

from arc_agent.policies import CyclicPolicy, RandomPolicy


class PolicyTests(unittest.TestCase):
    def test_cycle_uses_advertised_actions_in_order(self) -> None:
        policy = CyclicPolicy()
        self.assertEqual(policy.select([2, 4]).value, 2)
        self.assertEqual(policy.select([2, 4]).value, 4)
        self.assertEqual(policy.select([2, 4]).value, 2)

    def test_seeded_random_is_reproducible(self) -> None:
        first = RandomPolicy(17)
        second = RandomPolicy(17)
        self.assertEqual(
            [first.select([1, 2, 3]).value for _ in range(10)],
            [second.select([1, 2, 3]).value for _ in range(10)],
        )

    def test_empty_action_set_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CyclicPolicy().select([])

    def test_toolkit_action_identifiers_use_the_supported_conversion(self) -> None:
        self.assertEqual(CyclicPolicy().select([1]).name, "ACTION1")
