# ADR registry — vibecoding-copilot-governance

Decisions governing this repo and every repo synced from it. For the ADR folder shipped to
consumer projects, see `dev-factory/project-template/docs/adr/README.md`.

## Index

| ADR | Title | Status | Date | Relations |
|-----|-------|--------|------|-----------|
| [0001](ADR-0001-prd-adr-plan-runbook-methodology.md) | PRD → ADR → Plan → Runbook chain, two execution modes *(French, as authored)* | Accepted | 2026-09-14 | language clause superseded by 0002; Mode B superseded by 0005; Plan location amended by 0006; mode names by 0007 |
| [0002](ADR-0002-english-only-governance.md) | English as the sole governance language | Accepted | 2026-09-14 | supersedes 0001 (language clause) |
| [0003](ADR-0003-rename-family-prefix-vibecoding.md) | Rename family prefix `itshaker` → `vibecoding` | Accepted | 2026-09-15 | — |
| [0004](ADR-0004-hermes-local-default-execution.md) | Local model executes by default, frontier model by exception | Accepted | 2026-09-16 | extends 0001; amended by 0005 (who executes code) and 0007 |
| [0005](ADR-0005-sequential-claude-code-team-orchestrated-by-hermes.md) | Sequential Claude Code team (DEV/REVIEW/TEST) orchestrated by Hermes | Accepted | 2026-09-29 | supersedes 0001 Mode B; amends 0004; amended by 0007 (mode names, adapter) and 0008 (git model, kit sync) |
| [0006](ADR-0006-plans-in-docs-plans.md) | Delivery plans in `docs/plans/`, mandatory beyond three tasks | Accepted | 2026-10-05 | amends 0001 (Plan location) |
| [0007](ADR-0007-agent-neutral-project-contract-hermes-adapter.md) | Agent-neutral project contract; Hermes specifics in `adapters/hermes/` | Accepted | 2026-10-05 | amends 0001 (mode names), 0004, 0005 (where Hermes rules live) |
| [0008](ADR-0008-per-repo-agent-autonomy-levels.md) | Per-repository agent autonomy levels (`supervised`, `branch`, `trusted`) | Accepted | 2026-10-23 | amends 0005 (git model, kit sync); amended by 0009 (level `yolo`) |
| [0009](ADR-0009-autonomy-level-yolo.md) | Autonomy level `yolo`: agents merge their own PRs on green CI | Accepted | 2026-10-23 | amends 0008 (levels, rollback) and 0005 (human validation, at `yolo` only) |
| [0010](ADR-0010-coding-executors-claude-code-and-openhands.md) | Coding executors: Claude Code and OpenHands, declared per repository | Proposed | 2026-10-26 | amends 0005 (who is DEV), 0007 (adapters), 0008 (level file) |

Withdrawn (never accepted, kept for traceability, never implement from them):

| File | Why withdrawn |
|------|---------------|
| [withdrawn/ADR-0004-hermes-solo-local-default-execution.md](withdrawn/ADR-0004-hermes-solo-local-default-execution.md) | Concurrent draft of the same decision; the Capitaine kept the other ADR-0004 |

**Decisions in force, in one line each:** the PRD → ADR → Plan → Runbook/Task chain (0001);
everything in English (0002); `vibecoding-*` naming (0003); local model by default, frontier model
only on the closed criteria of `agents/runbook-generator.agent.md` (0004); code work by a
sequential Claude Code team orchestrated by Hermes, never by Hermes itself (0005); delivery plans
in `docs/plans/`, mandatory beyond three tasks (0006); projects are agent-neutral, orchestrator
specifics live in `adapters/` (0007); each repo declares its agents' autonomy level in
`.ai/autonomy.yaml` — `supervised` by default, `branch` or `trusted` — and humans always approve (0008),
except at `yolo` where the agent merges on green CI (0009); DEV runs on Claude Code or, where the repo
allows it, OpenHands in an isolated runner (0010, proposed).

## Rules

- **Numbering:** `ADR-NNNN-<slug>.md`, next free number, never reused — one number, one decision.
  Check `git fetch && ls docs/adr` before numbering: two sessions drafting in parallel is how
  0004 got two files.
- **Statuses:** Proposed · In progress · Accepted · Rejected · Withdrawn · Deprecated ·
  Superseded by ADR-NNNN. Partial supersession names the clause
  ("language clause superseded by ADR-0002").
- **Immutability:** once Accepted, the body is not rewritten. A changed decision is a new ADR
  that supersedes or amends the old one. Allowed edits to an accepted ADR, and only these:
  1. the **Status** line;
  2. a dated **Registry note** blockquote under the header fields (corrections, pointers);
  3. link maintenance (a path that moved);
  4. restoring authored text altered by tooling, verbatim from git history, with a registry note.
- **Bulk search/replace never touches `docs/adr/`** — exclude it explicitly (see the 0003
  registry note: its own rename rewrote it).
- **Withdrawn drafts** move to `withdrawn/`; they keep their number in the file name but no
  longer occupy it in the index.
- **Update this index** in the same commit as any ADR creation or status change.
