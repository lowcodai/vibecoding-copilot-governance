# ADR-0007 — Agent-neutral project contract; Hermes specifics move to a governance adapter

**Date:** 2026-10-05
**Status:** Accepted (2026-10-05, Capitaine)
**Decision-makers:** Capitaine (Jérémie Coste)
**Technical context:** governance + bootstrap + five `vibecoding-template-*` repos; sequential Claude Code team (ADR-0005); plans in `docs/plans/` (ADR-0006).
**authored_by:** frontier-model
**execution_mode:** single-agent (documentation, governance and template change; no application code)
**amends:** ADR-0001 (execution mode names), ADR-0004 and ADR-0005 (where Hermes-specific rules live)

## Context

- **CTX-001**: Every project receives `.hermes.md` (88 lines). It mixes rules any long-running
  agent needs (state files in `docs/operations/`, checkpoints, definition of done) with rules that
  only hold for one Hermes installation: the `write_file` silent-failure workaround
  (NousResearch/hermes-agent#119389), the `/opt/data/operations/` anchor, a per-model token table
  including frontier models, references to the external `HermesVPS2` repo and its ADR-0021.
- **CTX-002**: The ADR schema names the agent: `execution_mode: hermes-solo |
  hermes-sequential-team`. Replacing or adding an orchestrator would change the schema itself.
- **CTX-003**: Copies drifted. On 2026-10-05 all five templates still carried a 65,536-token
  `.hermes.md`, a methodology copy describing the OpenHands mode removed by ADR-0005, and stale
  `runbook-generator`/`adr-generator` copies — while `AGENTS.md` and the dev factory kit, which are
  drift-tested, were current.
- **CTX-004**: The execution core (ADR-0005: `scripts/orchestrate.py`, `.ai/`, `.claude/`) does
  not depend on Hermes: any orchestrator or a human can run it. The coupling is in conventions and
  copied documents, not in code.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Status quo | No work | Hermes workarounds in every project; schema names the agent; copies keep drifting |
| Keep `.hermes.md`, add drift tests only | Stops drift | Still ships installation-specific rules to every project; schema unchanged |
| **Agent-neutral project contract + Hermes adapter in governance + drift-tested copies** | Projects carry only portable rules; Hermes specifics in one place; schema survives an agent change; drift caught | One-time migration; old ADRs keep the old mode names |

## Decision

- **DEC-001 — Neutral project contract.** A project contains only agent-neutral material:
  `AGENTS.md`, `CLAUDE.md`, `.ai/`, `.claude/`, `scripts/orchestrate.py` and
  `docs/{prd,adr,plans,runbooks,operations}`. No `.hermes.md`.
- **DEC-002 — Continuity is a project rule.** The portable part of the former `.hermes.md`
  becomes a short **Continuity** section of `AGENTS.md` (state files, checkpoint triggers,
  context-pressure steps in percent, definition of done) plus `docs/operations/README.md`.
- **DEC-003 — Hermes adapter.** Everything specific to Hermes lives in governance under
  `adapters/hermes/` and is installed in Hermes' own environment, never copied into projects:
  `HERMES.md` (gateway limits in tokens, write verification workaround, out-of-repo anchor,
  escalation models) and `skills/sequential-coding-team/` (moved from `dev-factory/hermes-skill/`).
  Another orchestrator gets its own `adapters/<name>/`.
- **DEC-004 — Neutral execution modes.** `execution_mode` takes `orchestrated-team` (formerly
  `hermes-sequential-team`) or `single-agent` (formerly `hermes-solo`). ADR-0001 to ADR-0006 keep
  their values as authored; the old names remain valid aliases when reading them. No tool parses
  this field.
- **DEC-005 — Roles, not names.** Project documents say "the orchestrator" (Hermes today). Runbooks
  are executed by the orchestrator agent in `single-agent` mode, not "by Hermes" by definition.
- **DEC-006 — One home for the project skeleton.** The `docs/` skeleton READMEs and
  `docs/operations/` files move from governance `hermes/docs-*-templates/` into
  `dev-factory/project-template/docs/`, so `sync-governance.sh` and the template kit drift test
  cover them like the rest of the kit. Governance `hermes/` is removed.
- **DEC-007 — Copies are drift-tested or absent.** Any governance file copied into a template
  (`.github/agents|instructions|hooks`, PR and issue templates, `docs/methodology/`) must be
  identical to its governance source, enforced by a bootstrap test.

## Consequences

### Positive
- **POS-001**: An orchestrator change touches `adapters/` only, not every project or the ADR schema.
- **POS-002**: Installation workarounds stop leaking into projects created by other people.
- **POS-003**: The class of files that drifted (CTX-003) is now covered by tests.

### Negative
- **NEG-001**: Hermes must be configured once from `adapters/hermes/` (skill + global context)
  instead of finding its rules in each repo.
- **NEG-002**: Existing projects keep an obsolete `.hermes.md` until someone deletes it;
  `sync-governance.sh` no longer writes it and flags it.

### Neutral / To monitor
- **NEU-001**: If a Hermes version only reads per-project context files, a project may add a
  local, uncommitted pointer to `AGENTS.md`; the governance does not ship one.

## Implementation

- **IMP-001**: Governance: `adapters/hermes/{README.md,HERMES.md,skills/sequential-coding-team/SKILL.md}`;
  `hermes/docs-*-templates/` → `dev-factory/project-template/docs/` (+ `docs/operations/README.md`);
  `hermes/` removed; mode names updated in `templates/ADR-template.md`,
  `templates/RUNBOOK-template.md`, `agents/adr-generator.agent.md`,
  `agents/runbook-generator.agent.md`, the methodology and the ADR registry; neutral wording in the
  kit (`orchestrate.py`, `.ai/roles/dev.md`, task template, `orchestration.yaml`).
- **IMP-002**: Bootstrap: `sync-governance.sh` drops `sync_hermes` (flags an existing `.hermes.md`),
  the docs skeleton comes with `sync_dev_factory`; `apply-template.sh` renders a neutral `AGENTS.md`
  with a Continuity section; new `tests/test-template-governance-copies.sh` (DEC-007).
- **IMP-003**: Templates: delete `.hermes.md`; refresh the kit, `AGENTS.md` and governance copies;
  neutral README wording.
- **Error behaviour**: none at runtime — no tool reads `.hermes.md` or `execution_mode`.
- **Rollback condition**: if Hermes cannot be configured globally and loses its continuity
  discipline in practice, restore a per-project adapter file through a new ADR.

## References

- **REF-001**: ADR-0001, ADR-0004, ADR-0005, ADR-0006.
- **REF-002**: `adapters/hermes/README.md` — how to install the adapter.
