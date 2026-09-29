# ADR registry — vibecoding-copilot-governance

Decisions governing this repo and every repo synced from it. For the ADR folder shipped to
consumer projects, see `hermes/docs-adr-templates/README.md`.

## Index

| ADR | Title | Status | Date | Relations |
|-----|-------|--------|------|-----------|
| [0001](ADR-0001-prd-adr-plan-runbook-methodology.md) | PRD → ADR → Plan → Runbook chain, two execution modes *(French, as authored)* | Accepted | 2026-09-14 | language clause superseded by 0002; Mode B superseded by 0005 once accepted |
| [0002](ADR-0002-english-only-governance.md) | English as the sole governance language | Accepted | 2026-09-14 | supersedes 0001 (language clause) |
| [0003](ADR-0003-rename-family-prefix-vibecoding.md) | Rename family prefix `itshaker` → `vibecoding` | Accepted | 2026-09-15 | — |
| [0004](ADR-0004-hermes-local-default-execution.md) | Local model executes by default, frontier model by exception | Accepted | 2026-09-16 | extends 0001; amended by 0005 (who executes code) |
| [0005](ADR-0005-sequential-claude-code-team-orchestrated-by-hermes.md) | Sequential Claude Code team (DEV/REVIEW/TEST) orchestrated by Hermes | **Proposed** | 2026-09-29 | supersedes 0001 Mode B; amends 0004 |

Withdrawn (never accepted, kept for traceability, never implement from them):

| File | Why withdrawn |
|------|---------------|
| [withdrawn/ADR-0004-hermes-solo-local-default-execution.md](withdrawn/ADR-0004-hermes-solo-local-default-execution.md) | Concurrent draft of the same decision; the Capitaine kept the other ADR-0004 |

**Decisions in force, in one line each:** the PRD → ADR → Plan → Runbook/Task chain (0001);
everything in English (0002); `vibecoding-*` naming (0003); local model by default, frontier model
only on the closed criteria of `agents/runbook-generator.agent.md` (0004); pending 0005 —
code work by a sequential Claude Code team orchestrated by Hermes.

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
