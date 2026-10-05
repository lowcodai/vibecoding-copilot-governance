# ADR-0006 — Delivery plans live in `docs/plans/`; mandatory beyond three tasks

**Date:** 2026-10-05
**Status:** Accepted (2026-10-05, Capitaine)
**Decision-makers:** Capitaine (Jérémie Coste)
**Technical context:** PRD → ADR → Plan → Task/Runbook chain (ADR-0001), sequential Claude Code team (ADR-0005), Hermes on a 98k-context / 2k-output gateway.
**authored_by:** frontier-model
**execution_mode:** hermes-solo (documentation and governance change only)
**amends:** ADR-0001 (location and status of the Plan artifact)

## Context

- **CTX-001**: ADR-0001 put Plans in `.hermes/plans/*.md`: a hidden, Hermes-specific folder holding
  session-style breakdowns. Plans there are rarely reviewed in pull requests and are invisible to
  other agents and to humans browsing `docs/`.
- **CTX-002**: Since ADR-0005, code work is a series of task contracts (`.ai/tasks/TASK-NNNN.md`)
  run one at a time by `scripts/orchestrate.py`. The orchestrator has no notion of order or
  dependency between tasks, and `docs/operations/CURRENT.md` only tracks the active task.
- **CTX-003**: `BACKLOG.md` lists epics without sequencing, dependencies or links to tasks.
- **CTX-004**: Hermes sessions rotate (98k context). Without a plan on disk, a new session cannot
  tell which task comes next, which ones are done, or why they were cut that way.
- **CTX-005**: Epics express user value and derive from the PRD; the ADR decides how. Neither
  document says in which order the work is delivered.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Status quo (`.hermes/plans/` + `BACKLOG.md`) | No change | Plans hidden and unreviewed; ordering lost between sessions |
| Epics and task lists inside `BACKLOG.md` | One file | Grows unbounded; mixes the index of all epics with the breakdown of each; too large for a 2k-output writer |
| GitHub Issues/Projects as the plan of record | Rich tooling | Not readable offline by the local agents; outside the versioned repo |
| **`docs/plans/PLAN-NNNN-<slug>.md`, one per ADR or large epic, mandatory beyond 3 tasks** | Visible, reviewed in PRs, agent-agnostic, survives session rotation; small ADRs stay lightweight | One more document type to maintain |

## Decision

- **DEC-001**: Delivery plans live in **`docs/plans/PLAN-NNNN-<slug>.md`**, numbered per repo
  from 0001, using `templates/PLAN-template.md`. `.hermes/plans/` is no longer used for new plans;
  existing files stay as historical records.
- **DEC-002**: A plan is **mandatory** when the work linked to an ADR (or a PRD) needs **more than
  3 tasks**, spans **more than one epic**, has **dependencies** between tasks, or is expected to
  span **several Hermes sessions**. Otherwise Hermes goes from the ADR straight to task contracts,
  each citing the ADR in `adrs:`.
- **DEC-003**: A plan contains: links to its PRD and ADR(s); epics (`E1`, `E2`, …), each with a goal,
  an exit criterion and dependencies; a task table (`ID | epic | depends on | type | status`) where
  type is `task` (`.ai/tasks/`) or `runbook` (`docs/runbooks/`); risks and open points.
- **DEC-004**: Traceability both ways: task contracts gain `plan:` and `epic:` front-matter fields;
  the plan lists every task it spawned. `BACKLOG.md` becomes an index of epics, each linking to its
  plan when one exists.
- **DEC-005**: Single source of truth for status. A task's detailed state is in
  `.ai/runs/TASK-NNNN/state.json`; Hermes copies the terminal state (`READY_FOR_APPROVAL`,
  `APPROVED`, `BLOCKED`, merged) into the plan's task table. `BACKLOG.md` carries epic status only.
- **DEC-006**: Plans are sized for the local model: ≲ 3k tokens per file (split a large ADR into
  one plan per epic), written by Hermes in several verified edits (2k output cap), and reviewed in
  a pull request before the first task of the plan runs.
- **DEC-007**: Task contracts stay in `.ai/tasks/`; no `docs/tasks/` folder. They are machine
  inputs consumed by the orchestrator, already committed, and reachable from the plan.

## Consequences

### Positive
- **POS-001**: Ordering and progress survive Hermes session rotation.
- **POS-002**: Humans review the breakdown once, before agents spend hours on it.
- **POS-003**: Full chain PRD → ADR → PLAN → TASK/RUNBOOK → run → PR, navigable in both directions.

### Negative
- **NEG-001**: One more artifact for Hermes to keep current at each terminal state.
- **NEG-002**: Status is copied (run state → plan) rather than computed; it can lag if Hermes skips
  the update.

### Neutral / To monitor
- **NEU-001**: A future `orchestrate.py` command could regenerate the plan's status column from
  `.ai/runs/`, removing NEG-002.
- **NEU-002**: The 3-task threshold is a heuristic; revise it here if plans prove too heavy or too
  rare.

## Implementation

- **IMP-001**: `templates/PLAN-template.md` (new) and `hermes/docs-plan-templates/README.md` (new,
  copied to `<project>/docs/plans/README.md`).
- **IMP-002**: `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`: Plan location, the DEC-002
  rule, where Plan / Task / Runbook fit.
- **IMP-003**: `dev-factory/project-template/.ai/tasks/TASK-template.md`: `plan:` and `epic:`
  fields. `dev-factory/hermes-skill/sequential-coding-team/SKILL.md`: create or update the plan
  before writing tasks; update its task table at each terminal state.
- **IMP-004**: `standards/documentation-standards.md`: `docs/plans/` in the required structure,
  `BACKLOG.md` as an epic index. `templates/RUNBOOK-template.md`: "Source Plan" points to
  `docs/plans/`.
- **IMP-005**: `vibecoding-bootstrap`: `sync-governance.sh` creates `docs/plans/` with its README;
  `apply-template.sh` creates the folder, adds it to the `AGENTS.md` repository map and generates
  `BACKLOG.md` as an epic index. The `vibecoding-template-*` repos ship `docs/plans/README.md`, the
  re-rendered `AGENTS.md` and the updated task template.
- **Error behaviour**: a task contract whose `plan:` points to a missing plan is a framing error;
  Hermes fixes the reference before running the task. The orchestrator ignores both fields.
- **Rollback condition**: if plans are routinely left stale after real use, drop DEC-002 back to
  "optional" in a new ADR and keep `docs/plans/` for large work only.

## References

- **REF-001**: ADR-0001 — chain PRD → ADR → Plan → Runbook (Plan location amended here).
- **REF-002**: ADR-0005 — sequential Claude Code team; task contracts in `.ai/tasks/`.
- **REF-003**: `templates/PLAN-template.md`, `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`.
