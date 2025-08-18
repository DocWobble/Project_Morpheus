
```markdown
# PLAYBOOK.md

> Minimal rhythm for moving the repo forward without ceremony.

## Daily Rhythm (Agent)

1. **Sync:** pull main, scan diffs, read top of `GOALS.md`.
2. **Pick:** choose the smallest task that advances an active capability.
3. **Plan:** note touched surfaces and scenes to update (short list).
4. **Act:** implement; keep branch short-lived.
5. **Verify:** run scenes; extend where your change reveals new invariants.
6. **Record:** append `DECISIONS.log` if you made a trade-off; update `INTERFACES.md` if shapes changed.
7. **Merge:** if gates pass. Otherwise, shrink scope and try again.

## Weekly Rhythm

- **Prune:** deprecate dead code behind flags; remove once scenes prove safety.
- **Consolidate:** collapse duplicate helpers; reduce surfaces.
- **Stress:** run failure-injection scenes; capture regressions as new scenes.

## Release Rhythm

- Cut a tag only when scenes are green and `GOALS.md` shows at least one capability moved to **active** since last tag.
- Create a short `CHANGES.md` entry: capability-level deltas, not commit lists.

