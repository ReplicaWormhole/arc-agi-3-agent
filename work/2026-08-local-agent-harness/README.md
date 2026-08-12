# Local agent harness

## Question

How can we run and compare deterministic ARC-AGI-3 exploration policies against
locally cached games without API access?

## Scope

This workline implements an offline runner and deliberately simple policies.
It does not infer a game rule, train a model, or claim generalization.

## Current status

`arc_agent.runner` writes one JSONL record per initial observation and action.
The `cycle` and seeded `random` policies only choose actions exposed by each
observation. `arc_agent.explorer` adds an on-policy transition graph and a
hypothesis ledger: it balances coverage of legal action types, never repeats an
observed exact state-action pair, accepts only two-consistent-observation action
claims, and enables planning only through already observed progress routes.

This is a conservative first layer, not yet a semantic simulator: a claim such
as "ACTION1 changes the rendered state" is not a claim to have identified a
move direction or game objective.  A later object/state parser and model
proposer must make those stronger claims falsifiable.

## Checks

```bash
python -m unittest discover -s work/2026-08-local-agent-harness/tests -v
python work/2026-08-local-agent-harness/run_baseline.py --game ls20 --policy cycle --max-actions 8
python work/2026-08-local-agent-harness/run_explorer.py --game ls20 --max-actions 8
```

## Risks

Cached environments may not represent the competition evaluation distribution.
The toolkit's scorecard is separate from the harness log and may create its own
local state.

## Next action

Use traces from controlled action sweeps to define a compact observation and
state-difference representation for a first world-modeling baseline.
