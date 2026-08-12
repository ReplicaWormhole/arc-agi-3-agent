# Parallel work protocol

## Start a track

Create an isolated worktree and branch:

```bash
git worktree add ../arc-agi-3-<track> -b agent/<track>
```

Open an issue or write a short topic README that names the question, owned
paths, assumptions, expected artifact, and acceptance test.

## Ownership rules

- One agent owns one implementation path at a time.
- Treat `arc_agent` public interfaces, `pyproject.toml`, `.github/`, and root
  docs as shared: coordinate a change before editing them.
- Agents may read shared JSONL traces but only the episode executor writes the
  canonical action trace.
- Keep alternative methods in separate dated `work/` directories until an
  ablation supports integration.

## Handoff

Every handoff states the commit, command run, result, changed files, unresolved
risks, and next falsifiable action. Never summarize a hypothesis as a fact
without citing the trace/experiment that tested it.
