# ARC-AGI-3 competition workspace

This workspace develops reproducible, offline-capable agents for the
[ARC Prize 2026 ARC-AGI-3 competition](https://arcprize.org/competitions/2026/arc-agi-3).
It is an MIT-licensed public research codebase; no hidden-game solutions,
recordings, credentials, or model weights belong in the repository.

The first active workline is
`work/2026-08-local-agent-harness/`.  It provides a small runner for cached
ARC-AGI environments, deterministic baseline policies, and JSONL run logs.

Run the current baseline from this directory:

```bash
python work/2026-08-local-agent-harness/run_baseline.py --game ls20 --policy cycle --max-actions 32
# Or inspect the legal moves without repeating an observed state-action pair:
python work/2026-08-local-agent-harness/run_explorer.py --game ls20 --max-actions 16
```

The runner uses the toolkit's offline mode and expects downloaded environments
under `environment_files/`; it never requires an API call.

## Development

```bash
uv sync --all-extras
uv run python -m unittest discover -s work/2026-08-local-agent-harness/tests -v
uv run ruff check .
```

`uv.lock` is committed so CI and local development resolve the same dependency
set. `python -m pip install -e '.[dev]'` remains a supported fallback.

The project deliberately separates agent reasoning from model hosting. See
[the architecture](docs/architecture.md), [model backends](docs/model-backends.md),
and the [experiment protocol](docs/experiment-protocol.md).

## Collaboration

Use one branch/worktree per investigation and one owner per implementation
path. The shared action executor and observation log are protected interfaces;
read [parallel-work.md](docs/parallel-work.md) before starting a new agent task.

`writing/` is reserved for user-requested manuscript-facing material,
`sources/` for external source packets, and `archive/` for inactive work.
