# Plan template

```markdown
# PLAN-NNNN — <delivery title>

**Date:** YYYY-MM-DD
**Status:** Draft | Approved | In progress | Done | Abandoned
**PRD:** docs/prd/PRD-NNNN-<slug>.md  <!-- or "none" for a purely technical ADR -->
**ADR(s):** docs/adr/ADR-NNNN-<slug>.md
**Owner:** Hermes (orchestrator) · reviewed by <!-- human -->

<!-- ADR-0006: a plan is mandatory beyond 3 tasks, more than one epic, dependencies between
     tasks, or several Hermes sessions. Keep this file under ~3k tokens (split per epic if
     needed) and write it in several verified edits (2k output cap). Review it in a PR before
     the first task runs. -->

## Goal

<!-- One or two sentences: what is delivered when every epic below is done. -->

## Epics

### E1 — <user-visible outcome>
- **Goal:** <!-- the value delivered -->
- **Exit criterion:** <!-- verifiable: "a user can …", "the pipeline …" -->
- **Depends on:** — <!-- or E2, … -->

### E2 — <user-visible outcome>
- **Goal:**
- **Exit criterion:**
- **Depends on:** E1

## Tasks

<!-- One row per unit of work. type = task (.ai/tasks/, run by scripts/orchestrate.py) or
     runbook (docs/runbooks/, executed by Hermes). A task = one DEV run, < ~400 changed lines,
     verifiable acceptance criteria. Status is copied from the run at each terminal state:
     planned | running | READY_FOR_APPROVAL | APPROVED | merged | BLOCKED. -->

| ID | Epic | Summary | Depends on | Type | Status |
|----|------|---------|------------|------|--------|
| TASK-0001 | E1 | <!-- --> | — | task | planned |
| TASK-0002 | E1 | <!-- --> | TASK-0001 | task | planned |
| RUNBOOK-0001 | E2 | <!-- --> | TASK-0002 | runbook | planned |

## Risks and open points

- <!-- anything that could invalidate the order or require a new ADR -->

## Log

<!-- Dated one-liners for re-planning decisions (task split, reordering, abandoned epic). -->
```
