import json
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
PROJECT = HARNESS.parents[1]
sys.path.insert(0, str(HARNESS))

from arc_agent.policies import CyclicPolicy
from arc_agent.runner import run_episode


class RunnerTests(unittest.TestCase):
    @unittest.skipUnless(
        (PROJECT / "environment_files" / "ls20").exists(),
        "requires a locally cached ls20 environment",
    )
    def test_offline_episode_writes_actionable_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            summary = run_episode(
                game_id="ls20",
                policy=CyclicPolicy(),
                policy_name="cycle",
                seed=0,
                max_actions=3,
                environments_dir=PROJECT / "environment_files",
                output_dir=temporary_directory,
            )
            trace = Path(summary.trace_path)
            records = [json.loads(line) for line in trace.read_text().splitlines()]

        self.assertEqual(summary.actions_taken, 3)
        self.assertEqual(records[0]["event"], "reset")
        self.assertEqual([record["action_id"] for record in records[1:]], [1, 2, 3])
        self.assertEqual(len(records), 4)
        self.assertIn("frame_sha256", records[0]["observation"])

    def test_nonpositive_budget_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_episode(
                game_id="ls20",
                policy=CyclicPolicy(),
                policy_name="cycle",
                seed=0,
                max_actions=0,
            )
