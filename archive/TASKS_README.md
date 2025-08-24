# TASKS/README.md

> How to write tasks the agent can execute without losing the plot.

## Task Spec (must include)

- **WHY:** tie to `GOALS.md` capability or add one.
- **OUTCOME:** operational capability achieved (not “change X to Y”).
- **SURFACES TOUCHED:** files/modules/apis/clis/schemas.
- **SCENES:** which to create/extend; success = scenes pass.
- **RISK:** what can break; how to roll back safely.
- **SIZE:** target 1–3 commits; small, reversible.
- **MERGE GATE:** list scenes that gate the PR.

## Execution Rules

- Draft plan → implement → extend scenes → run scenes → update `DECISIONS.log` and `INTERFACES.md` as needed → merge.
- If a task becomes multi-day, split it; land scaffolding with feature flag.
- Refuse tasks that cannot point to a goal or lack a compatibility plan.
- Never introduce a new dependency without a line in `DECISIONS.log`.

## Commit Messages

`feat|fix|refactor(core|api|cli|data): <capability|surface> — <short outcome>`

Example style (not content):  
`feat(api): durable retries — request-scoped idempotency keys`

## PR Description Checklist

- [ ] WHY and OUTCOME present
- [ ] Scenes added/updated
- [ ] Interfaces documented
- [ ] Decision logged
- [ ] Rollback path

