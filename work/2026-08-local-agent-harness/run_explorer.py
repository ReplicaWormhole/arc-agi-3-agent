"""Run one on-policy ARC-AGI-3 exploration episode against a cached game."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from arc_agent.explorer import ExplorationController
from arc_agent.runner import DEFAULT_LOG_DIR, frame_observation
from arc_agi import Arcade
from arc_agi.base import OperationMode
from arcengine import GameState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", default="ls20")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-actions", type=int, default=16)
    parser.add_argument("--environments-dir", type=Path, default=Path("environment_files"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_LOG_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_actions < 1:
        raise ValueError("max-actions must be positive")
    arcade = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(args.environments_dir),
    )
    env = arcade.make(args.game, seed=args.seed)
    if env is None:
        raise FileNotFoundError(f"no cached environment matching {args.game!r}")
    frame = env.reset()
    if frame is None:
        raise RuntimeError("could not reset environment")

    controller = ExplorationController()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = (
        args.output_dir / f"explore-{frame.game_id}-seed{args.seed}-{uuid4().hex[:8]}.jsonl"
    )
    with trace_path.open("x", encoding="utf-8") as trace:
        for index in range(args.max_actions):
            if frame.state != GameState.NOT_FINISHED:
                break
            action = controller.select_exploration_action(frame)
            mode = "explore"
            if action is None and controller.planning_ready(frame):
                action = controller.select_planned_action(frame)
                mode = "planned"
            if action is None:
                break
            next_frame = env.step(action)
            if next_frame is None:
                raise RuntimeError(f"environment failed after {action.name}")
            transition = controller.observe(frame, action, next_frame)
            trace.write(
                json.dumps(
                    {
                        "index": index + 1,
                        "mode": mode,
                        "action": action.name,
                        "transition": transition.__dict__,
                        "observation": frame_observation(next_frame),
                        "report": controller.report(next_frame),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            frame = next_frame
    result = {"trace_path": str(trace_path), "final_report": controller.report(frame)}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
