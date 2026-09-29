# ADR-0005 — Sequential Claude Code team (DEV / REVIEW / TEST) orchestrated by Hermes

**Date:** 2026-09-29
**Status:** Proposed
**Decision-makers:** Capitaine (Jérémie Coste)
**Technical context:** DGX Spark (Founders Edition), vLLM serving `Qwen-3.8-27B-NVFP4`, one gateway per agent role, Hermes as Engineering-Manager agent, Claude Code as the coding runtime.
**authored_by:** frontier-model
**execution_mode:** hermes-solo (documentation and governance change only)
**supersedes:** the Mode B (`hermes-orchestrator-openhands`) part of ADR-0001 and of `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`
**amends:** ADR-0004 (who executes code on the local model — the model-tier default is unchanged)
**source:** "ADR-XXX — Orchestration séquentielle d'une équipe Claude Code pilotée par Hermes" (Capitaine, 2026-09-29)

## Context

- **CTX-001**: A single inference model (`Qwen-3.8-27B-NVFP4`) runs on a single DGX Spark.
  Parallel coding agents compete for the GPU, multiply KV caches and lower total throughput.
- **CTX-002**: Code work today is either done by Hermes itself (Mode A, `hermes-solo`) or
  delegated to OpenHands (Mode B). Mode B was never qualified outside `hermes-spark-builder`
  (no GitHub token for `--repo` conversations, no stable conversation ids) and assumes
  parallel sandboxes the hardware cannot sustain. Mode A mixes the author and the reviewer of
  the same code in one context: no independent verdict.
- **CTX-003**: Claude Code is the chosen coding runtime. It speaks the Anthropic Messages API
  and can target a local gateway (`ANTHROPIC_BASE_URL`), runs headless (`claude -p`), and can be
  restricted per invocation (`--tools`, `--bare`, `--settings`).
- **CTX-004**: Each role is served through its own gateway on the same model:

  | Gateway | Role | Context | Max output | Temperature |
  |---|---|---:|---:|---:|
  | `hermes-orchestrator` | Hermes | 98k | 2k | 0.2 |
  | `cc-dev` | Claude Code DEV | 98k | 4k | 0.2 |
  | `cc-review` | Claude Code REVIEW | 32k | 2k | 0.1 |
  | `cc-test` | Claude Code TEST | 32k | 2k | 0.1 |

  These values replace the draft figures of the source document (REVIEW 32k/3k/0.10,
  TEST 16k/2k/0.05), and the 65,536-token figure previously documented in `hermes/.hermes.md`.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Keep Mode A (Hermes codes alone) | No new tooling | No independent review; Hermes' 2k output cap is too small to write code efficiently; mixes management and implementation context |
| Keep Mode B (OpenHands, parallel roles) | Strong isolation | Unqualified outside one host; parallelism wastes a single-GPU box; second agent runtime to maintain |
| **Sequential Claude Code roles driven by a state machine, Hermes orchestrates** | One active agent at a time; independent REVIEW/TEST verdicts; each role gets only the context it needs; resumable and auditable | Slower than true parallelism; an orchestrator script to maintain; requires disciplined task contracts |

## Decision

- **DEC-001**: Code work runs as a **logical team executed sequentially**: Hermes
  (orchestrator) → Claude Code DEV → Claude Code REVIEW → Claude Code TEST → human validation →
  merge. At any time: one model, one active Claude Code role (`max_concurrent_agents: 1`).
- **DEC-002**: Hermes plans, writes task contracts, runs the orchestrator, arbitrates results and
  prepares the human validation. **Hermes does not write code and never merges.**
- **DEC-003**: New `execution_mode` value **`hermes-sequential-team`** — the default for any ADR
  that changes code. `hermes-solo` remains for documentation, governance and Runbook-driven
  operations. `hermes-orchestrator-openhands` is deprecated: existing ADRs keep it as written;
  new ADRs must not use it.
- **DEC-004**: Workflow and loop-backs:
  `PLANNED → DEV → REVIEW (CHANGES_REQUESTED → DEV) → TEST (FAIL → DEV) → READY_FOR_APPROVAL →
  human validation → merge`. REVIEW verdicts: `ACCEPTED | CHANGES_REQUESTED | BLOCKED`.
  TEST verdicts: `PASS | FAIL | BLOCKED`. Loops are bounded; exceeding a bound ends in `BLOCKED`.
- **DEC-005**: Validation commands are executed **by the orchestrator**, not by an LLM. The TEST
  role interprets exit codes and logs; a non-zero exit code can never produce `PASS`.
- **DEC-006**: Git model: 1 task = 1 branch (`agent/TASK-NNNN`) = 1 worktree, reused by DEV,
  REVIEW and TEST in turn. Agents commit locally; push, merge and rebase are denied.
- **DEC-007**: Context is budgeted per role: DEV gets the task contract and reads
  AGENTS.md/ADR/PRD itself (98k); REVIEW gets acceptance criteria, ADR Decision/Implementation
  excerpts and the diff (32k); TEST gets acceptance criteria and validation results (32k).
  REVIEW and TEST run with `--bare` (no CLAUDE.md auto-load, hooks, memory, prefetch) so that
  Claude Code's own overhead fits in 32k.
- **DEC-008**: Temperature, output caps, per-route context caps and Qwen thinking mode are
  **enforced by the gateways** (Claude Code does not expose temperature).
- **DEC-009**: The model-tier default of ADR-0004 is unchanged (local model by default,
  frontier model on the closed escalation criteria of `agents/runbook-generator.agent.md`).
  What changes is the executor: on the local model, code is written by Claude Code DEV, not by
  Hermes.

## Consequences

### Positive
- **POS-001**: Best use of a single DGX Spark: no GPU contention, one KV cache in use for coding.
- **POS-002**: Independent verdicts: REVIEW and TEST run in fresh contexts and cannot be
  overwritten by DEV; TEST cannot contradict a red command.
- **POS-003**: Resumable and auditable: every run persists `state.json`, per-role results,
  validation logs and a timeline under `.ai/runs/TASK-NNNN/`.
- **POS-004**: Removes a second agent runtime (OpenHands) from the governance scope.

### Negative
- **NEG-001**: Wall-clock time is higher than a parallel system.
- **NEG-002**: `scripts/orchestrate.py` and the gateways must be maintained.
- **NEG-003**: 32k REVIEW/TEST budgets cap the reviewable diff (≈ 45–55k characters after
  overhead): tasks must stay small (< ~400 changed lines). Oversized diffs are truncated
  head+tail and flagged in the work order.
- **NEG-004**: Hermes' 2k output cap forces task contracts to stay short (< ~1,200 tokens) and
  to be written in several verified edits.

### Neutral / To monitor
- **NEU-001**: `overhead_tokens` per role (Claude Code system prompt + tool schemas) is an
  estimate; calibrate it from the `usage` lines the orchestrator writes to `timeline.log`.
- **NEU-002**: Claude Code sub-agents (`Task`/`Agent` tools) are disabled to keep execution
  strictly sequential; revisit if the hardware changes.

## Implementation

- **IMP-001**: `dev-factory/project-template/` — files copied into every consumer repo:
  `.ai/orchestration.yaml` (project contract), `.ai/tasks/TASK-template.md` (task contract),
  `.ai/roles/{dev,review,test}.md` (role prompts and JSON result contracts),
  `.claude/settings.json` (deny rules), `CLAUDE.md` (short, no AGENTS.md import),
  `scripts/orchestrate.py` (state machine).
- **IMP-002**: `dev-factory/gateways.yaml` — reference gateway profiles and the enforcement
  checklist (temperature override, max_tokens clamp, per-route prompt cap, thinking off).
- **IMP-003**: `dev-factory/hermes-skill/sequential-coding-team/SKILL.md` — the Hermes skill.
- **IMP-004**: `dev-factory/tests/test_orchestrate.py` — state-machine tests with a fake agent
  (`python3 -m unittest discover -s dev-factory/tests`).
- **IMP-005**: Governance alignment: `hermes/.hermes.md` (98k Hermes thresholds + per-gateway
  table), `templates/ADR-template.md` and `templates/RUNBOOK-template.md` (`execution_mode`
  values), `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md` (Mode B replaced),
  `agents/runbook-generator.agent.md` and `agents/adr-generator.agent.md` (context figures).
- **IMP-006**: `vibecoding-bootstrap/scripts/sync-governance.sh` gains `sync_dev_factory`
  (copy-if-not-exists, never overwrites a project's tuned `orchestration.yaml`).
- **Error behaviour**: any agent error, timeout, unparseable result (after 1 retry) or exceeded
  loop bound ends the run in `BLOCKED`; the orchestrator never guesses a verdict.
- **Rollback condition**: if three consecutive real tasks end `BLOCKED` for tooling reasons
  (not task reasons), revert consumer repos to `hermes-solo` for code by removing `.ai/` and
  reopening this ADR.

## References

- **REF-001**: ADR-0001 — chain PRD → ADR → Plan → Runbook (Mode B superseded here).
- **REF-002**: ADR-0002 — English-only governance.
- **REF-003**: ADR-0004 — local model by default (`ADR-0004-hermes-local-default-execution.md`).
- **REF-004**: `docs/analysis/2026-09-29-governance-audit.md` — audit that motivated this ADR.
