# ADR-0009 — Autonomy level `yolo`: agents merge their own pull requests on green CI

**Date:** 2026-10-23
**Status:** Accepted (2026-10-23, Capitaine)
**Decision makers:** Capitaine (Jérémie Coste)
**Technical context:** autonomy levels of ADR-0008 (`supervised`, `branch`, `trusted`); Arcane (Hermes) on
3M6 driving `scripts/orchestrate.py`; repositories without branch protection on private GitHub Free plans.
**authored_by:** frontier-model
**execution_mode:** single-agent (governance and kit change, implemented and tested in this repo and in
`vibecoding-bootstrap`)
**amends:** ADR-0008 (DEC-001 levels table; rollback condition), ADR-0005 (DEC-002/DEC-004 human validation —
at level `yolo` only)

## Context

- **CTX-001**: ADR-0008 stops at `trusted`: an agent may merge its own green PR in an interactive session, but
  an orchestrated task still waits for `orchestrate.py approve` by a human.
- **CTX-002**: The Capitaine needs Arcane to commit, push and merge on its own in `arcane3m6`, without waiting
  for a human, while keeping every change reviewable after the fact and every check enforced.
- **CTX-003**: ADR-0008's rollback condition sets every repo back to `supervised` when an agent action reaches
  the base branch without human review — exactly what this level allows by design.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Use `trusted` and approve every task | No new level | A human is still in the loop for every task |
| `yolo` with direct pushes to `main` | Fastest | No CI before the change lands; no reviewable unit; irreversible without branch protection |
| **`yolo` through pull requests, merged by the agent on green CI; red CI sent back to the agent** | No human gate; CI always runs first; every change is a PR that can be read and reverted | Merges as fast as CI allows; a wrong change that passes CI lands unreviewed |

## Decision

- **DEC-001 — Fourth level `yolo`**, least restrictive, after `trusted`. Declared in `.ai/autonomy.yaml` like the
  others; the most-restrictive rule, the protected file and the `supervised` fallback of ADR-0008 apply unchanged.
- **DEC-002 — Everything goes through a pull request.** No push to the base branch at any level, `yolo`
  included. The agent pushes its own branch, opens a ready (not draft) PR and merges it with `--squash`.
- **DEC-003 — Green CI before merge; the agent fixes red CI.** A PR is merged only when every check passes (a
  repo with no check configured is merged once none has appeared within a grace period). In an orchestrated run
  a red CI sends the task back to DEV with the failing checks and their logs; DEV fixes, REVIEW and TEST run again,
  the branch is pushed to the same PR, and CI is awaited again, at most `limits.max_ci_cycles` times (default 3),
  then `BLOCKED`. In an interactive session the agent reads the failing logs (`gh run view --log-failed`), fixes and
  pushes until green, then merges.
- **DEC-004 — No human approval at `yolo`.** The orchestrator merges at `READY_FOR_APPROVAL` once CI is green;
  the task ends `APPROVED` with `merge.by: orchestrator (autonomy yolo)`. The human is informed after the fact
  (merged PR, `state.json`, `timeline.log`). DEV itself still never pushes or merges.
- **DEC-005 — Invariants unchanged** (ADR-0008 DEC-002): no force push, rebase or history rewrite; no push to
  the base branch; no merge on red checks, no `--admin`, no `--no-verify`; no secrets read or committed; no
  `sudo`, recursive deletion of roots or exfiltration; `gh api` read-only; no change to protected paths (an agent
  never edits its own guard rails or level); no publication or infrastructure change outside a Runbook.
- **DEC-006 — Rollback condition replaced.** ADR-0008's condition no longer applies to `yolo` merges. A repo at
  `yolo` goes back to `trusted` (and this ADR is reopened) when an agent merge turns the base branch's CI red, or
  when an agent change to a protected path reaches the base branch.

## Consequences

### Positive
- **POS-001**: Arcane delivers end to end on `arcane3m6` with no human wait, CI still enforced.
- **POS-002**: Every change remains a squash-merged PR: readable, attributable, revertible.

### Negative
- **NEG-001**: A wrong change that passes CI lands without review; CI quality becomes the safety net.
- **NEG-002**: Without branch protection the client-side checks and the orchestrator are the only barriers in
  front of the base branch.

### Neutral / To monitor
- **NEU-001**: `max_ci_cycles` and `ci_timeout_sec` (in `.ai/orchestration.yaml` → `limits`) bound the loop;
  tune them per repo.

## Implementation

- **IMP-001**: Kit: `yolo` in `autonomy.py` (deny rules as `trusted`, `CLAUDE.md`/`AGENTS.md` blocks),
  `tool_guardian.py` (gh write for `pr`, `issue`, `run rerun`; own green PR merge), `orchestrate.py` (ready PR,
  CI wait, merge on green, red CI back to DEV with logs, `max_ci_cycles`), limits in `orchestration.yaml`,
  `autonomy.yaml` comment; docs and Hermes skill.
- **IMP-002**: Bootstrap: `--autonomy yolo` accepted by `new-project.sh`, `sync-governance.sh`, `apply-template.sh`.
- **IMP-003**: Tests: hook at `yolo`; orchestrator green → merged without approval, red → DEV with logs → merged,
  still red → `BLOCKED`, no CI → merged, no PR → `BLOCKED`.
- **IMP-004**: `arcane3m6` moves to `yolo` (Capitaine's decision, 2026-10-23).
- **Error behaviour**: CI timeout, merge failure or missing PR end the task `BLOCKED` with the reason logged.

## References

- **REF-001**: ADR-0008 — per-repository autonomy levels (amended here).
- **REF-002**: ADR-0005 — sequential Claude Code team (amended at `yolo`).
