---
name: sequential-coding-team
description: Drive one coding task through the sequential Claude Code team (DEV → REVIEW → TEST → human approval) with scripts/orchestrate.py. Use when a repo contains .ai/orchestration.yaml and the user asks Hermes to implement, fix or refactor something. Hermes plans, writes the task contract, runs the orchestrator, arbitrates and reports; it never codes and never merges.
---

# Sequential coding team (ADR-0005)

Budget reminder: you run on the `hermes-orchestrator` gateway (98k context, 2k output,
temperature 0.2). Keep every write small and verify it (`.hermes.md` § Write verification).

## 1. Frame the work
1. Read `AGENTS.md`, `.ai/orchestration.yaml`, and the PRD/ADRs relevant to the request.
2. If the request needs an architecture decision no ADR makes: stop and propose an ADR
   (adr-generator) to the user first. Never push an undecided choice onto DEV.
3. Split into tasks small enough for one DEV run (target: < 400 changed lines each).

## 2. Write the task contract
1. `python3 scripts/orchestrate.py new TASK-NNNN --title "<title>"` (next free number).
2. Fill `.ai/tasks/TASK-NNNN.md` in at most two edits (front matter + sections), each under
   ~1,500 tokens; read the file back after each edit.
3. Mandatory: Objective, Scope, Out of scope, Acceptance criteria (verifiable AC-n lines),
   `adrs:` list, task-specific `validations:` if the project-wide ones do not cover the ACs.

## 3. Run
1. Start `python3 scripts/orchestrate.py run TASK-NNNN` in the background (terminal tool);
   it may run for a long time. Do not generate while it runs: poll with
   `orchestrate.py status TASK-NNNN` and `tail -n 20 .ai/runs/TASK-NNNN/timeline.log`
   at a slow interval.
2. Checkpoint `docs/operations/CURRENT.md` before starting and after each terminal state.

## 4. Arbitrate the terminal state
- `READY_FOR_APPROVAL` → summarise for the human: branch, commits (`git log base..branch`),
  review summary, validation results. Wait for their decision. On approval run
  `orchestrate.py approve TASK-NNNN --by "<name>"`; the human merges.
- `BLOCKED` → read the last `*-result.json` and `timeline.log`. Classify:
  - ADR gap / contradiction → propose an ADR amendment; do not rewrite the task to dodge it.
  - loop limit reached → narrow the task or split it; restart with a new TASK number.
  - environment / validation misconfigured → fix the config with the human, then
    `orchestrate.py rework TASK-NNNN --feedback "<what changed>"`.
  - escalation criteria of `agents/runbook-generator.agent.md` met → escalate as documented.
- Human rejects → `orchestrate.py rework TASK-NNNN --feedback "<their words>"` and run again.

## Never
- Edit code, run DEV/REVIEW/TEST yourself, or start two runs at once (the lock will refuse).
- Push, merge, rebase, or approve on the human's behalf.
- Edit `.ai/runs/**` or loosen `.ai/orchestration.yaml` limits to get a task through.
