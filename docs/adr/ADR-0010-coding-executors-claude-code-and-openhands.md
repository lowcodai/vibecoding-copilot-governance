# ADR-0010 — Coding executors: Claude Code and OpenHands, declared per repository

**Date:** 2026-10-26
**Status:** Proposed — accepted when the Capitaine merges this ADR
**Decision makers:** Capitaine (Jérémie Coste)
**Technical context:** dev factory kit (`dev-factory/project-template/`), Arcane (Hermes) on the Mac mini 3M6 with
the Docker socket mounted, OpenHands 1.8 app and OpenHands CLI 1.16 available on 3M6, vLLM on the DGX Spark
serving `dgx-spark-current` (Qwen 3.8 27B, 131,072-token window) with both the OpenAI and the Anthropic Messages
API.
**authored_by:** frontier-model
**execution_mode:** single-agent (governance and kit change, implemented and tested in this repo and in
`vibecoding-bootstrap`)
**amends:** ADR-0005 (DEC-001 who is DEV, POS-004), ADR-0007 (DEC-003 adapters), ADR-0008 (DEC-003 content of the
level file, NEU-001)

## Context

- **CTX-001**: OpenHands is back on 3M6 and Arcane can drive it (the Hermes `openhands` skill, installed on
  2026-10-26). The Capitaine wants it as a complement to Claude Code for **long development sessions**, not as a
  replacement.
- **CTX-002**: ADR-0005 removed OpenHands from governance (DEC-003, POS-004). The kit knows one executor:
  `scripts/orchestrate.py` launches `claude -p` and parses its JSON envelope.
- **CTX-003**: Every repo-level guard rail is Claude Code specific (ADR-0008 NEU-001): deny rules in
  `.claude/settings.json`, `tool_guardian.py`, `secrets_scanner.py`. OpenHands reads none of them. Only the
  orchestrator's own gates are agent-neutral: protected paths, `autonomy-check`, `secrets-scan`, validations,
  REVIEW/TEST verdicts, push/PR/merge done by the orchestrator.
- **CTX-004**: The installed Hermes skill runs the OpenHands CLI headless **inside Arcane's container**
  (`LocalWorkspace`, `NeverConfirm`). That container runs as root, holds Arcane's data and secrets and has the
  Docker socket: an OpenHands run there controls the whole Colima VM.
- **CTX-005**: The orchestrated Claude Code team has never run on Arcane: no `claude` binary in its container, no
  `.ai/runs/` in any repo, and the per-role gateways of `dev-factory/gateways.yaml` (ports 4001–4003) do not exist.
  vLLM serves `/v1/messages` directly.
- **CTX-006**: A long session does not fit the ADR-0005 task size: REVIEW reads the whole diff in 32k tokens,
  which caps a task at about 400 changed lines.
- **CTX-007**: One model on one GPU (`max_num_seqs: 2`). The repository lock does not stop two coding agents in
  two repos from sharing it.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Keep OpenHands out of governance; Arcane uses the generic skill | No work | Unguarded runs with Arcane's privileges (CTX-004); no review, no gates; work invisible to the PR flow |
| Restore Mode B (`hermes-orchestrator-openhands`, one OpenHands conversation per role) | Strong isolation per role with the OpenHands app | Second state machine; REVIEW/TEST by the same runtime that wrote the code; the ADR-0005 objections still hold |
| **OpenHands as a second DEV executor of the orchestrated team, allowed per repo, run in an isolated runner** | One state machine and one set of gates for both agents; REVIEW/TEST stay independent; the repo owner decides which agents may code | An executor adapter and a runner image to maintain; Claude Code hooks do not apply to OpenHands |

## Decision

- **DEC-001 — Two DEV executors.** The DEV role of the orchestrated team (ADR-0005) runs on `claude-code` (default)
  or `openhands`. REVIEW and TEST stay Claude Code with read-only tools, so an OpenHands change is always judged
  by another runtime. `execution_mode` values are unchanged: OpenHands returns as an executor inside
  `orchestrated-team`, not as a mode; `hermes-orchestrator-openhands` stays deprecated.
- **DEC-002 — The repo declares which agents may code.** `.ai/autonomy.yaml` gains
  `executors: [claude-code]` (default and fallback). The effective list is the **intersection** of the
  working-tree file and its copy on the base branch, like the level (ADR-0008 DEC-003): adding `openhands` takes
  effect only once a human has merged it. Changed with `sync-governance.sh --executors <list>`.
- **DEC-003 — The task chooses.** A task contract may set `executor:` (default `claude-code`). A value the repo
  does not allow ends the run `BLOCKED` before DEV starts.
- **DEC-004 — OpenHands only through the orchestrator, only in an isolated runner.** No orchestrator agent runs
  OpenHands directly on a governed repo, and never in its own environment. The runner where the DEV executor runs
  must meet this contract:
  1. the executor runs as an unprivileged user, distinct from the user that runs `orchestrate.py`;
  2. no container-runtime socket, no `sudo`;
  3. no forge or git credentials reachable by that user: the orchestrator pushes (ADR-0008);
  4. no secret in its environment other than the LLM key; the environment is rebuilt from an allow-list;
  5. no access to the orchestrator agent's data: only the runner's own clones and worktrees.
  Network egress stays open (package registries, the LLM); with no credential to use, this is the accepted
  residual risk.
- **DEC-005 — Gates for OpenHands are the orchestrator's.** Protected paths, `autonomy-check`, `secrets-scan`,
  project validations, REVIEW, TEST, and push/PR/merge by the orchestrator apply unchanged. Claude Code hooks and
  deny rules do not apply to OpenHands; DEC-004 is what contains it while it works.
- **DEC-006 — Long sessions.** OpenHands gets its own timeout (default 4 h) and must commit each logical step
  separately, each under ~400 changed lines. When a task diff exceeds the REVIEW budget, the orchestrator reviews it
  **by chunks of consecutive commits** that fit the budget, one REVIEW call per chunk; the task verdict is the worst
  chunk verdict (`BLOCKED` > `CHANGES_REQUESTED` > `ACCEPTED`) and findings are merged. This applies to both
  executors. A single commit larger than the budget is truncated head+tail and flagged, as today.
- **DEC-007 — Headless means no questions.** An executor cannot wait for a human: the "Ask first" cases of
  `AGENTS.md` end DEV with `status: BLOCKED` and the question in `reason`, for the orchestrator to escalate.
- **DEC-008 — One coding agent per model.** `execution.shared_lock` (optional path in `.ai/orchestration.yaml`) is
  taken in addition to the repo lock, so runners that share a model serialise across repos.
- **DEC-009 — Who does what.**

  | Lane | Work | Executor | Model |
  |---|---|---|---|
  | A — interactive Claude Code with the Capitaine | PRD/ADR, infrastructure, production, security, secrets, incidents, escalations of ADR-0004 | Claude Code (interactive) | frontier |
  | B — orchestrated, `executor: claude-code` | small, well-bounded tasks (< ~400 changed lines) | Claude Code DEV | local |
  | C — orchestrated, `executor: openhands` | long sessions: an epic of a plan, a multi-hour build/test loop, many files | OpenHands DEV | local |

  The orchestrator picks B or C when it writes the task contract, C only when the repo allows `openhands`.
  REVIEW and TEST are the same in B and C.
- **DEC-010 — OpenHands gateway profile.** OpenHands speaks the OpenAI API: its route is declared as an
  `openai` gateway (`oh-dev`: 98k context, 8k output, temperature 0.2) and reaches the executor as `LLM_MODEL`,
  `LLM_BASE_URL`, `LLM_API_KEY` with `--override-with-envs`.
- **DEC-011 — Adapters.** `adapters/openhands/` documents the runner contract (DEC-004) and the CLI invocation;
  `adapters/hermes/` gains the routing rule of DEC-009 and forbids the generic Hermes `openhands` skill on
  governed repos.

## Consequences

### Positive
- **POS-001**: Long sessions become possible without giving up the PR flow, the gates or independent review.
- **POS-002**: The repo owner, not the orchestrator, decides which agents may change a repo, and an agent cannot
  widen that list.
- **POS-003**: Chunked review also lifts the ~400-line ceiling for Claude Code tasks made of small commits.
- **POS-004**: OpenHands no longer runs with the orchestrator's privileges.

### Negative
- **NEG-001**: OpenHands works without per-command hooks; a destructive command inside the runner is caught only
  by isolation and by the gates after DEV.
- **NEG-002**: A runner image (OpenHands CLI, Claude Code CLI, git, gh) and an executor adapter to maintain;
  OpenHands CLI output formats change between versions: the version is pinned in the runner.
- **NEG-003**: Several REVIEW calls per large task cost more local-model time.

### Neutral / To monitor
- **NEU-001**: Calibrate the OpenHands timeout and the chunk size on the first real tasks (`timeline.log`).
- **NEU-002**: GitHub Copilot keeps its own guard rails; this ADR governs orchestrated runs.

## Implementation

- **IMP-001 (kit, `dev-factory/project-template/`)**:
  `.claude/hooks/autonomy.py` — `EXECUTORS = ("claude-code", "openhands")`, `parse_executors`,
  `effective_executors(root)` (intersection, fallback `["claude-code"]`), `render --executors`, `check`;
  `.ai/autonomy.yaml` — `executors: [claude-code]`;
  `.ai/orchestration.yaml` — `gateways.oh-dev` (`api: openai`), `agents.dev.executors.openhands`
  (`gateway`, `role_prompt`, `timeout_sec`, `command`), `execution.shared_lock` (commented);
  `.ai/roles/dev-openhands.md` — DEV prompt for long sessions (commit per step, BLOCKED instead of questions);
  `.ai/tasks/TASK-template.md` — `executor:`;
  `scripts/orchestrate.py` — executor selection and check (DEC-003), OpenHands adapter (work order as a file,
  JSONL parsing: final `FinishAction` message, else last agent message), chunked REVIEW (DEC-006), shared lock
  (DEC-008).
- **IMP-002 (kit tests)**: executor allowed / refused / fallback, OpenHands JSONL parsing with a fake CLI, chunked
  review verdict aggregation, shared lock contention, intersection of executors lists.
- **IMP-003 (governance docs)**: `dev-factory/README.md`, `adapters/openhands/README.md`, `adapters/hermes/`
  skill (routing, no generic `openhands` skill on governed repos), methodology, ADR registry.
- **IMP-004 (bootstrap)**: `--executors <list>` on `new-project.sh`, `sync-governance.sh`, `apply-template.sh`;
  `AGENTS.md` role table gains the OpenHands DEV row and the headless rule; templates ship `[claude-code]`.
- **IMP-005 (3M6, `lowcodai/3m6-config`)**: a `dev-runner` container meeting DEC-004 (users `orchestrator` and
  `agent`, no socket, environment allow-list, its own clones and GitHub token), driven by Arcane through
  `docker exec`; Arcane is briefed to stop using the generic `openhands` skill.
- **Error behaviour**: unknown or disallowed executor, missing CLI, unparseable OpenHands output (after the retry
  of ADR-0005) or timeout end the task `BLOCKED` with the reason logged; the orchestrator never guesses a verdict.
- **Rollback condition**: three consecutive OpenHands tasks `BLOCKED` for tooling reasons, or any OpenHands run
  that reaches outside its worktree or runner, sets every repo back to `executors: [claude-code]` and reopens this
  ADR.

## References

- **REF-001**: ADR-0005 — sequential coding team (amended here).
- **REF-002**: ADR-0007 — agent-neutral project contract, adapters.
- **REF-003**: ADR-0008, ADR-0009 — autonomy levels.
- **REF-004**: `lowcodai/3m6-config` `docker/openhands/` and RUNBOOK-0012 (OpenHands on 3M6).
