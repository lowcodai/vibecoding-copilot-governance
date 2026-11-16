# ADR-0011 — `yolo` interactive sessions: protected paths, base-branch sync, private-network uploads

**Date:** 2026-11-16
**Status:** Accepted (2026-11-16, Capitaine)
**Decision makers:** Capitaine (Jérémie Coste)
**Technical context:** autonomy level `yolo` (ADR-0009) on `arcane3m6`; interactive Claude Code sessions tuning
the orchestrated team (`.ai/orchestration.yaml`, role prompts) and measuring the local model (vLLM on the DGX Spark).
**authored_by:** frontier-model
**execution_mode:** single-agent (kit change, implemented and tested in this repo)
**amends:** ADR-0008 (DEC-002 invariants and DEC-004 protected paths — at level `yolo`, interactive sessions only),
ADR-0009 (DEC-005 invariants, DEC-006 rollback condition)

## Context

- **CTX-001**: On 2026-11-16 an interactive `yolo` session on `arcane3m6` had to stop and hand work back to the
  Capitaine three times: to edit `.ai/orchestration.yaml` (protected), to update the local `main` after merging
  its own PR (`git switch main`, `git pull`), and to send a captured request to the local vLLM to count tokens
  (`curl --data-binary @file` to `192.168.1.25`, treated as exfiltration).
- **CTX-002**: At `yolo` the agent already merges its own PRs with no human review (ADR-0009). The protected-path
  invariant was the remaining human gate; the Capitaine chose to remove it for interactive sessions.
- **CTX-003**: Orchestrated runs (DEV/REVIEW/TEST driven by `scripts/orchestrate.py`) run a 27B local model on task
  contracts; they must not change the team's own configuration.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Keep every invariant; the human applies patches the agent prepares | Agent never edits its own guard rails | One human action per configuration change |
| Unlock project-tuned files only (`.ai/orchestration.yaml`, `.ai/roles/`) | Removes most of the friction; hooks stay out of reach | `.claude/`, the level and the orchestrator still need a human |
| **Unlock every protected path, plus base-branch sync and private-network uploads, in interactive `yolo` sessions only** | No human step left in interactive work | The agent can weaken or disable its own hooks and merge that on green CI |

## Decision

- **DEC-001 — Scope.** The relaxations below apply only when the effective level is `yolo` **and** the session is
  interactive (`ORCHESTRATE_ROLE` unset). Every other level and every orchestrated run keeps ADR-0008/ADR-0009
  unchanged. The effective level is still the most restrictive of the working tree and the base branch
  (ADR-0008 DEC-003), so an edit of `.ai/autonomy.yaml` can lower the level at once but never raise it unmerged.
- **DEC-002 — Protected paths.** `.claude/`, `.ai/autonomy.yaml`, `.ai/orchestration.yaml`, `.ai/roles/` and
  `scripts/orchestrate.py` may be edited, through the file tools and the shell. The change still goes through a PR
  merged on green CI (ADR-0009 DEC-002/DEC-003). Kit-owned files edited in a repo are overwritten by the next sync
  (ADR-0008 DEC-007).
- **DEC-003 — Base-branch sync.** `git switch <base>` / `git checkout <base>` (only `-q` as a flag) and
  `git pull --ff-only` (optionally `origin <base>`, `-q`) are allowed. Committing on, pushing to and merging into
  the base branch stay forbidden.
- **DEC-004 — Uploads to the private network.** `curl` and `wget` may send local files when every URL in the
  command has an explicit scheme and a host that is loopback, private (RFC 1918), link-local or ends in `.local`.
  Uploads anywhere else, and downloads piped to a shell, stay forbidden.
- **DEC-005 — Enforcement.** At `yolo`, `.claude/settings.json` no longer denies `git pull`, `git checkout main`,
  `git switch main` or edits of the protected paths; `tool_guardian.py` enforces DEC-002 to DEC-004 structurally.
  `orchestrate.py` adds the protected-path `Edit(...)` rules to `--disallowedTools` of every orchestrated run, and
  its protected-paths diff check is unchanged.
- **DEC-006 — Rollback condition.** ADR-0009 DEC-006 is replaced: a repo at `yolo` goes back to `trusted` when an
  agent merge turns the base branch's CI red, or when an agent change disables the secrets scanner, the
  `secrets-scan` validation or `tool_guardian.py` on the base branch.

## Consequences

### Positive
- **POS-001**: An interactive session tunes the orchestrated team, keeps its checkout current and measures the
  local model end to end, with no human step.

### Negative
- **NEG-001**: The agent can change or disable its own hooks, deny rules, level file and orchestrator, and merge
  that on green CI. CI and after-the-fact reading of merged PRs are the only barriers left.
- **NEG-002**: Copilot hooks (`hooks/` at the root of this repo) are not changed by this ADR and stay stricter.

### Neutral / To monitor
- **NEU-001**: Read merged PRs touching `.claude/` or `.ai/` after the fact; DEC-006 is the trigger to step back.

## Implementation

- **IMP-001**: `autonomy.py`: `deny_rules("yolo")` without the relaxed rules; `disallowed_tools("yolo")` carries the
  protected-path `Edit(...)` rules for orchestrated runs; `yolo` blocks of `CLAUDE.md`/`AGENTS.md` updated.
- **IMP-002**: `tool_guardian.py`: relaxed checks for interactive `yolo` (DEC-002 to DEC-004).
- **IMP-003**: Tests: interactive `yolo` allows the relaxed commands and still blocks their unsafe variants;
  orchestrated `yolo` and every other level still block all of them.
- **IMP-004**: `arcane3m6` picks the change up with `sync-governance.sh` (bootstrap).

## References

- **REF-001**: ADR-0008 — per-repository autonomy levels (amended here).
- **REF-002**: ADR-0009 — autonomy level `yolo` (amended here).
