# ADR-0004 — Hermes-on-local-model executes by default; frontier model is the exception

**Date:** 2026-09-16
**Status:** Accepted
**Decision-makers:** Capitaine (Jérémie Coste), Arcane (Hermes)
**Technical context:** lowcodai governance ecosystem (templates, Copilot agents, methodology) — repo `vibecoding-copilot-governance` (currently `itshaker-copilot-governance` on disk, pending ADR-0003 rename completion).
**authored_by:** frontier-model (this ADR is authored by Claude Sonnet 5, at the Capitaine's request, 2026-09-16)
**execution_mode:** hermes-solo (this ADR's own documentation work, and the three implementation deliverables it authorizes, are single-repo, documentation-only, and reversible — no role isolation is required)

## Context

ADR-0001 established the PRD → ADR → Plan → Runbook chain and two execution modes (Mode A —
Hermes Solo; Mode B — Hermes Orchestrator + OpenHands), plus a model-tier recommendation that
covers **only PRD and ADR**: "a frontier model is strongly recommended... a local model is
allowed... never a tooling gate" (`docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`,
§"Model tier recommendation"). That recommendation is silent on which model tier actually executes
**Plan, Runbook, dev, test, and security** downstream of an accepted ADR — `execution_mode`
(`hermes-solo` / `hermes-orchestrator-openhands`) only picks a role-isolation strategy, not a model
tier. In practice this leaves the choice of executing model an implicit, case-by-case judgment
call, with no documented default and no explicit escalation criteria.

Two structural gaps compound this:

1. **The chain stops at the ADR in practice.** `templates/RUNBOOK-template.md` and
   `agents/runbook-generator.agent.md` are referenced by ADR-0001 and by
   `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md` since 2026-09-14, but neither file exists.
   There is no way today to hand a local model a Runbook dense and unambiguous enough to execute
   without re-arbitrating architecture along the way.
2. **The ADR "Implementation" section is optional guidance, not a contract.** Both
   `templates/ADR-template.md` and `agents/adr-generator.agent.md` treat implementation detail as
   "if applicable" / "practical guidance" rather than a binding set of file paths, data contracts,
   error behavior, and rollback conditions. A local model with a bounded context window cannot
   safely generalize a Plan/Runbook from an ADR that leaves architecture decisions implicit.

The Capitaine's direction (2026-09-16): Hermes running on the local model
(`unsloth/Qwen3.8-27B-NVFP4`, DGX Spark, vLLM — 65,536-token context window, see
`hermes/.hermes.md`) should take on nearly all roles (architecture, dev, test, security) by
default, via Plan then Runbook, until an operational, functional, iteratively-improvable solution
is reached. Frontier-model involvement (Claude Sonnet 5, GPT-5.6 Sol) becomes the exception,
triggered by explicit, verifiable criteria — not a default caution reflex applied "just in case."

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Status quo — no documented default, model tier chosen case by case downstream of the ADR | No immediate effort | Leaves the exact gap this ADR exists to close; inconsistent behavior across sessions; no lever to reduce frontier-model cost by default |
| Frontier model by default, local model as the documented exception | Maximizes per-decision quality assurance | Directly contradicts the Capitaine's direction; keeps cost high by default; does not generalize the already-accepted Mode A pattern toward autonomy |
| **Local model executes by default (architecture/dev/test/security via Plan → Runbook), frontier model escalation on explicit criteria only** | Matches the Capitaine's direction; keeps cost low by default while preserving a documented, verifiable safety valve; forces the ADR "Implementation" contract and the Runbook guard-rail to be strengthened as a side effect, closing both structural gaps above | Requires the Runbook layer and the ADR contract hardening to exist first, or the local model has no guard-rail against silently deciding what the ADR left open |

## Decision

We adopt **local-model execution by default** for architecture, development, test, and security
roles, carried out by Hermes via Plan then Runbook until an operational, functional, and
iteratively-improvable solution is reached. Frontier-model involvement becomes the **exception**,
triggered only by the explicit, closed list of escalation criteria defined in
`agents/runbook-generator.agent.md` (infrastructure/production/security impact, significant
recurring cost, unresolved ambiguity after a bounded number of clarification attempts, or a
detected contradiction between the ADR and the real state of the code).

This decision is made possible, and is only made possible, by two guard-rails introduced in the
same change wave (see §Implementation):

- A Runbook must never introduce a decision absent from its linked ADR — if it encounters one, it
  stops and reports the gap instead of arbitrating it locally. This is what allows a 27B local
  model to stay within bounds without continuous frontier-model supervision.
- An ADR's "Implementation" section becomes a binding execution contract (exact file paths, data
  contracts, error behavior, rollback condition) instead of optional guidance, so that a Plan and a
  Runbook can be generalized from it without re-arbitrating architecture.

`execution_mode` (`hermes-solo` / `hermes-orchestrator-openhands`) is orthogonal to this decision:
it selects role-isolation strategy, not model tier, and is unaffected by this ADR.

## Consequences

### Positive
- **POS-001**: Generalizes the already-accepted Mode A pattern (ADR-0001) toward autonomous
  execution, reducing frontier-model cost by default across the ecosystem.
- **POS-002**: Forces the two structural gaps identified in §Context to close as a precondition of
  the decision, rather than leaving them as separate, lower-priority backlog items.
- **POS-003**: Escalation becomes auditable and verifiable (closed criteria list) instead of an
  implicit judgment call made differently by every session.

### Negative
- **NEG-001**: Quality risk on ambiguous or high-stakes decisions if the escalation criteria are
  incomplete or too narrowly scoped — mitigated by the Runbook stop-condition guard-rail (a gap the
  local model cannot silently paper over) and by the fact that the criteria list itself can be
  amended by a future ADR without reopening this one.
- **NEG-002**: Additional upfront documentation cost: every ADR targeting local-model execution
  must now satisfy a stricter "Implementation" contract and a density/length constraint before it
  can be handed downstream — slower ADR authoring in exchange for safer unattended execution.

### Neutral / To monitor
- **NEU-001**: Mode B (`hermes-orchestrator-openhands`) remains fully available and unaffected —
  this ADR concerns model tier, not role-isolation strategy.
- **NEU-002**: The recurring-cost escalation threshold (see `agents/runbook-generator.agent.md`) is
  a fixed figure that will likely need recalibration over time; revising it does not require
  reopening this ADR, only updating the agent's documented criteria.

## Implementation

- **IMP-001**: Create `templates/RUNBOOK-template.md` — front matter with mandatory `linked_adr`
  (never empty), `authored_by`, `execution_mode`, `status`; numbered steps, each with an exact
  verification command and, for at-risk steps, an explicit rollback condition; a mandatory
  stop-condition clause: a Runbook that needs a decision absent from `linked_adr` stops and reports
  the gap instead of deciding.
- **IMP-002**: Create `agents/runbook-generator.agent.md` — generates Runbooks written for
  `hermes-solo` execution on the local model by default: dense text, no elliptical steps, no step
  assuming an architectural inference not already written elsewhere. Documents the closed
  escalation-criteria list (infra/production/security impact, recurring cost above the documented
  threshold, unresolved ambiguity after the documented number of clarification attempts, ADR/code
  contradiction detected during execution).
- **IMP-003**: Harden `templates/ADR-template.md` and `agents/adr-generator.agent.md` —
  "Implementation" becomes a mandatory execution contract (exact file paths, data contracts, error
  behavior, rollback condition), never "if applicable"; add a density/length constraint tied to
  `execution_mode` when the target is local-model execution (coded bullets over prose, indicative
  length cap), referencing the 65,536-token context window documented in `hermes/.hermes.md`.
- **IMP-004**: Update `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md` to document this new
  default explicitly, fix the `docs/runbook/` → `docs/runbooks/` naming inconsistency against
  `vibecoding-template-base`, and reference `templates/RUNBOOK-template.md` /
  `agents/runbook-generator.agent.md` alongside the existing PRD/ADR references.
- **IMP-005**: Propagation of `runbook-generator` to consumer template repos
  (`vibecoding-template-base` and siblings) via `sync-governance.sh` and
  `config/awesome-copilot-bundles.yml` (in `vibecoding-bootstrap`) is tracked separately and is not
  part of this ADR's own implementation — it follows once IMP-001 through IMP-004 are accepted and
  merged.

## References

- **REF-001**: ADR-0001 — `docs/adr/ADR-0001-prd-adr-plan-runbook-methodology.md` (chain and
  execution-mode origin; this ADR extends its model-tier recommendation downstream of the ADR).
- **REF-002**: ADR-0002 — `docs/adr/ADR-0002-english-only-governance.md` (all documents produced
  under this ADR are written in English).
- **REF-003**: `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md` (updated by IMP-004).
- **REF-004**: `hermes/.hermes.md` (model context-window table — source of the 65,536-token figure
  for `unsloth/Qwen3.8-27B-NVFP4`).
- **REF-005**: `templates/ADR-template.md`, `agents/adr-generator.agent.md` (hardened by IMP-003).
