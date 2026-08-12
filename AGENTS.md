# ARC-AGI-3 agent workspace

## Scope and integrity

- This repository develops reproducible ARC-AGI-3 agents. The competition target
  is generalization to hidden games, not a high score on one public game.
- Keep agent code, experiments, checks, and generated run logs in a dated topic
  directory under `work/`. Do not edit `writing/` without an explicit request.
- Keep downloaded ARC environments in `environment_files/` unchanged. They are
  external benchmark artifacts and are intentionally Git-ignored.
- Treat a score improvement as empirical evidence only. Record the environment
  version, seed, action budget, model/configuration, command, and result before
  making a comparison claim.
- Never inspect environment source code, start parallel copies of a held-out
  game, use public solution traces, or allow a model to access the internet
  while evaluating a competition-like episode.

## Agent architecture

- The executor is the only component allowed to issue real environment actions.
  Model proposers and critics consume the immutable observation log only.
- Hypotheses must name their supporting transitions, predicted consequence, and
  a falsifying observation. Do not promote a hypothesis merely because it is
  plausible or an LLM is confident.
- Predictive simulators must replay recorded transitions before their plans can
  be executed. Stop a plan on its first prediction mismatch.
- The backend-neutral model interface may use a local or remote endpoint during
  development. A competition submission must not require network access.

## Parallel work

- Work from a separate branch/worktree: `agent/<short-track>`.
- Each agent owns one named path or module. Do not concurrently edit shared
  controller interfaces, root configuration, or another agent's workline.
- Read `docs/parallel-work.md`, `docs/architecture.md`, and the current topic
  README before editing. Record design decisions in `docs/decisions/`.
- Submit focused commits with tests. Do not merge, publish, submit to Kaggle,
  or upload recordings without current-turn user approval.

## Checks

- Run `python -m unittest discover -s work/2026-08-local-agent-harness/tests -v`
  for changes to the first harness.
- Run `ruff check .` when the development dependencies are installed.
- CI deliberately runs only model-free unit tests: no credentials, downloaded
  environments, or remotely hosted models are available in GitHub Actions.
