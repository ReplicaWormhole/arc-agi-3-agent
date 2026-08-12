"""CLI for repeatable offline ARC-AGI-3 baseline runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from arc_agent.policies import CyclicPolicy, RandomPolicy
from arc_agent.runner import run_episode, summary_json

WORKLINE = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", default="ls20", help="cached game ID or exact version")
    parser.add_argument("--policy", choices=("cycle", "random"), default="cycle")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-actions", type=int, default=32)
    parser.add_argument("--environments-dir", type=Path, default=Path("environment_files"))
    parser.add_argument("--output-dir", type=Path, default=WORKLINE / "logs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    policy = CyclicPolicy() if args.policy == "cycle" else RandomPolicy(args.seed)
    summary = run_episode(
        game_id=args.game,
        policy=policy,
        policy_name=args.policy,
        seed=args.seed,
        max_actions=args.max_actions,
        environments_dir=args.environments_dir,
        output_dir=args.output_dir,
    )
    print(summary_json(summary))


if __name__ == "__main__":
    main()
