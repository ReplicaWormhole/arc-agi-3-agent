"""Run an ARC-AGI-3 episode locally and emit portable, structured evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from arc_agi import Arcade
from arc_agi.base import OperationMode
from arcengine import FrameDataRaw, GameState

from .policies import Policy

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


@dataclass(frozen=True)
class RunSummary:
    game_id: str
    seed: int
    policy: str
    actions_taken: int
    levels_completed: int
    win_levels: int
    terminal_state: str
    trace_path: str


def frame_observation(frame: FrameDataRaw) -> dict[str, Any]:
    """Return a JSON-safe, compact summary without storing raw visual frames."""
    planes = frame.frame
    digest = hashlib.sha256()
    shapes: list[list[int]] = []
    for plane in planes:
        digest.update(plane.tobytes())
        shapes.append(list(plane.shape))
    return {
        "frame_sha256": digest.hexdigest(),
        "frame_shapes": shapes,
        "available_actions": list(frame.available_actions),
        "levels_completed": frame.levels_completed,
        "win_levels": frame.win_levels,
        "state": frame.state.name,
    }


def _write_jsonl(handle: Any, record: dict[str, Any]) -> None:
    handle.write(json.dumps(record, sort_keys=True) + "\n")


def run_episode(
    *,
    game_id: str,
    policy: Policy,
    policy_name: str,
    seed: int,
    max_actions: int,
    environments_dir: str | Path = "environment_files",
    output_dir: str | Path = DEFAULT_LOG_DIR,
) -> RunSummary:
    """Run one bounded offline episode and persist its observation/action trace."""
    if max_actions < 1:
        raise ValueError("max_actions must be positive")

    arcade = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(environments_dir),
    )
    env = arcade.make(game_id, seed=seed)
    if env is None:
        raise FileNotFoundError(f"no cached environment matching {game_id!r} in {environments_dir}")
    initial = env.reset()
    if initial is None:
        raise RuntimeError(f"could not reset {game_id!r}")

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    trace_path = path / f"{initial.game_id}-seed{seed}-{uuid4().hex[:8]}.jsonl"
    current = initial
    actions_taken = 0
    with trace_path.open("x", encoding="utf-8") as trace:
        _write_jsonl(
            trace,
            {
                "event": "reset",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "game_id": current.game_id,
                "seed": seed,
                "policy": policy_name,
                "observation": frame_observation(current),
            },
        )
        while actions_taken < max_actions and current.state == GameState.NOT_FINISHED:
            action = policy.select(current.available_actions)
            next_frame = env.step(action)
            if next_frame is None:
                raise RuntimeError(f"environment failed after {action.name}")
            actions_taken += 1
            current = next_frame
            _write_jsonl(
                trace,
                {
                    "event": "step",
                    "index": actions_taken,
                    "action": action.name,
                    "action_id": action.value,
                    "observation": frame_observation(current),
                },
            )

    return RunSummary(
        game_id=current.game_id,
        seed=seed,
        policy=policy_name,
        actions_taken=actions_taken,
        levels_completed=current.levels_completed,
        win_levels=current.win_levels,
        terminal_state=current.state.name,
        trace_path=str(trace_path),
    )


def summary_json(summary: RunSummary) -> str:
    """Render a machine-readable CLI result."""
    return json.dumps(asdict(summary), sort_keys=True)
