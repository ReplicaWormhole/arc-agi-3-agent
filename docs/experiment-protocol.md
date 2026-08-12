# Experiment protocol

## Unit of evidence

An experiment is a named configuration run on declared cached environments. A
single score, seed, or public game is not evidence of generalization.

For every run, preserve a JSONL trace containing:

- exact game version and seed;
- source revision and command;
- action budget and environment mode;
- model backend/model identifier, if one is used;
- every real action, prediction, observation, and mismatch;
- terminal state, levels completed, and efficiency result when available.

Keep traces under `work/<topic>/logs/`; they are ignored by Git unless a small,
deliberately scrubbed fixture is needed for a test.

GitHub CI runs the model-free tests and skips the cached-`ls20` integration
test because benchmark environments are intentionally not committed. Run that
integration test locally after downloading the environment.

## Development versus evaluation

Local development can use cached public environments and a remote model to
propose hypotheses. A competition-like evaluation must use one game client,
one trajectory, no source inspection, no extra client for counterfactual
testing, and no network access available to the decision system.

## Promotion gates

1. **Observed transition:** one executed action produced a recorded outcome.
2. **Accepted hypothesis:** at least two compatible observations and no known
   contradiction, with a stated falsifier.
3. **Verified simulator rule:** exactly replays all transitions in its declared
   evidence set.
4. **Executable plan:** reaches a target inside the simulator; executor checks
   every real predicted step and stops at the first mismatch.
5. **Comparative result:** replicated across declared games/seeds and compared
   with a frozen baseline.
