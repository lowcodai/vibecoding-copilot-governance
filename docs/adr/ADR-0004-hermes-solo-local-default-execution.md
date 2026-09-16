# ADR-0004 — Default execution tier for Plan/Runbook/dev/test/sec: Hermes on the local model, frontier model by exception

**Date:** 2026-09-16
**Status:** Proposed — Superseded by `ADR-0004-hermes-local-default-execution.md` (same decision number, independently drafted in a concurrent session on 2026-09-16 before either was pushed; the Capitaine chose to keep the other file — Status: Accepted, including the full IMP-001/002/003 implementation — as the authoritative ADR-0004. This document is kept as-authored, per the ADR immutability principle, for audit/traceability only; do not implement from it.)
**Decision makers:** Capitaine (Jérémie Coste), Arcane (Hermes)
**Technical context:** lowcodai governance ecosystem (templates, Copilot agents, methodology) — repo `vibecoding-copilot-governance`; applies to execution across every repo governed by this methodology.
**authored_by:** frontier-model (this document is drafted by Claude Sonnet 5 in this session)
**execution_mode:** hermes-solo (documentary/governance work — no OpenHands delegation needed)

## Context

ADR-0001 established the PRD → ADR → Plan → Runbook → execution chain and settled two
distinct axes for it:

- an `authored_by` field (`frontier-model` recommended, `local-model` allowed) for
  **decision artifacts** (PRD, ADR) only. `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`
  is explicit that this recommendation stops there: *"The Plan and the Runbook do not carry
  this recommendation: they are execution artifacts, not decision artifacts."*
- an `execution_mode` field (`hermes-solo` / `hermes-orchestrator-openhands`) with explicit
  selection criteria (isolation, parallelism, stakes) for *who orchestrates* execution — a
  single Hermes agent sequentially taking every role, versus Hermes delegating each role to
  an isolated OpenHands app-conversation.

What ADR-0001 never settled: once an execution mode is chosen — in practice almost always
`hermes-solo`, the only mode that is actually mature today (it executed ADR-0001 itself and
the ADR-0003 rename wave; Mode B remains gated on OpenHands prerequisites not met everywhere)
— **which model tier** drives Hermes while it executes the Plan/Runbook roles (architecture,
dev, test, security)? Nothing answers this today; each ADR is nominally left to arbitrate it
case by case, which in practice has never been done explicitly. ADR-0003 illustrates the
resulting confusion directly: its `authored_by` field reads `frontier-model
(Qwen3.8-27B-NVFP4)`, conflating the model-tier axis with the decision-authorship axis this
ADR now separates out.

Two changes in constraint justify answering this now rather than continuing to leave it
implicit:

- **Cost.** The volume of downstream execution work (dev/test/sec across the four template
  repos plus consumer repos such as `itshaker-dgx-spark-V2`, `HermesVPS2`, and future
  instantiated projects) far exceeds the volume of PRD/ADR authoring. Running a frontier
  model by default at that volume is not sustainable — the Capitaine already rejected a
  "frontier model mandatory" option for PRD/ADR authoring in ADR-0001, for cost reasons; the
  same argument applies with more force downstream, where volume is larger.
- **Maturity of Mode A.** `hermes-solo` (via the `subagent-driven-development` skill) is now
  a proven pattern in actual use — it executed ADR-0001 and the ADR-0003 rename wave — while
  Mode B still depends on OpenHands prerequisites (`oh_pilot.py` / `openhands-pilot`
  availability) that are not guaranteed on every target.

This ADR fills the gap: it fixes the default *model tier* for execution (Hermes on the local
model, by default), together with escalation criteria to a frontier model that are
objectively verifiable — not a generic reflex of caution.

**Scope note.** This decision is orthogonal to `execution_mode`. `execution_mode` (solo vs.
orchestrator-openhands, already settled by ADR-0001 / the workflow's §Modes) is unchanged by
this ADR. This ADR adds a second, independent axis — the *model tier* (local vs. frontier) —
which can vary without changing `execution_mode`: an escalation to a frontier model does not
by itself move Hermes out of `hermes-solo`. Hermes can stay in `hermes-solo` for a given task
while that task is, for the duration of the escalation, driven by a frontier model (Claude
Sonnet 5, GPT-5.6 Sol) instead of the local model.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Status quo — no explicit default, arbitrated case by case per ADR | Maximum flexibility, no imposed bias | Repeated arbitration overhead on every ADR; drifts toward an unstated, undocumented "frontier by caution" default; does not scale to the current execution volume |
| Frontier model by default for everything, local model by exception | Maximum quality/safety baseline, minimal drift risk | Cost-prohibitive at current volume (direct precedent: rejected by the Capitaine for PRD/ADR in ADR-0001, for cost reasons — applies more strongly downstream); contradicts the principle already applied (local model already allowed for reversible, low-stakes PRD/ADR); under-uses the proven maturity of Mode A |
| Local model by default for everything, frontier model by exception on explicit criteria (**retained**) | Cost aligned with the actual execution volume; extends a principle already accepted (local model for reversible/low-stakes work) instead of inventing a new one; capitalizes on Mode A's proven track record; keeps escalation available and rule-bound rather than removed | Quality-drift risk without a systematic frontier safeguard — ADR-0001's mitigation (`authored_by` + recommended frontier review before "Accepted") covers only PRD/ADR, not Plan/Runbook; requires rigorously verifiable escalation criteria so the exception does not become a meaningless checkbox |

## Decision

We choose **local model by default for hermes-solo execution, frontier model by exception on
explicit criteria** because it aligns cost with the actual volume of downstream execution
work, extends a principle already accepted for PRD/ADR authoring rather than inventing a new
one, and capitalizes on the proven maturity of Mode A instead of the still-partial Mode B.

By default, Hermes running on the local model (Qwen-3.8-27B-NVFP4, DGX Spark, vLLM — the
model identified as "default" in `hermes/.hermes.md`) takes on almost every role
(architecture, dev, test, security) in `execution_mode: hermes-solo`, until an operational,
functional solution is reached that can be improved through subsequent iterations. Recourse
to a frontier model (Claude Sonnet 5, GPT-5.6 Sol) is the exception, triggered only by the
explicit criteria below — never by a default reflex of caution.

### Escalation criteria

Each criterion below is individually sufficient to trigger escalation to a frontier model,
and each is written to be objectively constatable during execution — never a vague "if
needed" or "if complex enough" judgment call.

1. **Public infrastructure / production.** The task modifies infrastructure exposed
   publicly or a production deployment (e.g. reverse-proxy/DNS configuration, a public API
   surface, any path or resource already tagged `production`/`public` under the target
   repo's own conventions). Verifiable via file path or environment tag, not a value
   judgment.
2. **Sensitive data.** The task touches secrets, credentials, PII, or any path/config
   already classified as sensitive (e.g. anything requiring Doppler secret injection under
   existing `AGENTS.md` conventions, or a schema/table already classified as sensitive).
   Verifiable via an existing secret-management flag, not a subjective read.
3. **Significant recurring cost.** The task provisions or changes a resource whose
   recurring cost exceeds **$50/month** (a new paid API subscription, an always-on compute
   instance, a cloud resource billed monthly). Verifiable by comparing a stated dollar
   figure against the threshold, checkable against the service's invoice or quote.
4. **Ambiguity unresolved after 3 clarification attempts.** Hermes re-reads the source ADR,
   the Plan, and the relevant `.hermes/plans/` history, and performs up to 3 documented
   clarification passes (each logged as a checkpoint per the `hermes/.hermes.md`
   discipline). If the ambiguity is still unresolved after the 3rd attempt, escalation is
   mandatory rather than guessing. Verifiable via the count of documented clarification
   attempts against the threshold of 3.
5. **Contradiction between the ADR and the actual state of the code.** During execution,
   Hermes detects that the source ADR's decision rests on an assumption (a dependency, a
   version, an architectural fact) that the current state of the repo contradicts.
   Verifiable via an explicit diff between the ADR's assumption and the observed repo state
   (via code/`git` inspection), not an impression.

## Consequences

### Positive

- **POS-001**: Cost aligned with the actual execution volume, which is far larger than the
  PRD/ADR authoring volume — the bulk of execution runs on local inference with no
  per-token billing.
- **POS-002**: Faster iteration — Hermes on the local model can iterate without a round trip
  to an external API, consistent with the "until an operational solution is reached...
  improvable through subsequent iterations" framing of the decision (ship a working first
  pass fast rather than block on frontier-model availability).
- **POS-003**: Generalizes a pattern already proven in practice (Mode A / hermes-solo,
  already used to execute ADR-0001 and ADR-0003) instead of leaving it implicit.

### Negative

- **NEG-001**: Quality-drift risk without a systematic frontier safeguard at the execution
  layer. This should be stated honestly: ADR-0001's mitigation (`authored_by` audit field +
  recommended frontier review before "Accepted") covers only PRD/ADR — the workflow document
  explicitly states Plan and Runbook "do not carry this recommendation." This ADR therefore
  introduces a mitigation gap at the execution layer that it does not itself close — only the
  partial escalation criteria above apply. Closing this gap structurally (an audit discipline
  for Plan/Runbook equivalent to `authored_by`) is deferred to the follow-up work listed under
  Implementation.
- **NEG-002**: An escalation-criteria list is inherently incomplete and will need periodic
  recalibration as the execution track record grows — the same discipline `hermes/.hermes.md`
  already applies to its context-window table ("verify periodically... never assume").

### Neutral / To monitor

- **NEU-001**: Is this default global (every repo governed by `vibecoding-copilot-governance`)
  or overridable per repo / per ADR? ADR-0001 already left the equivalent question open for
  `execution_mode` ("The grain of `execution_mode` is chosen by ADR (not by repo)... to
  reconsider if the Capitaine prefers a per-repo default"). The same question is inherited
  here for the model-tier default and is not resolved by this ADR.

## Implementation

This ADR documents the decision only — no implementation is carried out here. Once accepted,
the following work is tracked in a **separate plan**:

- **IMP-001**: Author `templates/RUNBOOK-template.md` (does not exist yet), including a way
  to record the model tier actually used per step (local by default / frontier plus the
  triggered escalation criterion).
- **IMP-002**: Author `agents/runbook-generator.agent.md` (does not exist yet), analogous to
  `agents/adr-generator.agent.md`, expected to embed the 5 escalation criteria above as a
  pre-execution checklist.
- **IMP-003**: Reinforce `templates/ADR-template.md` and `agents/adr-generator.agent.md` with
  a way to declare/audit the expected execution model tier for a given ADR — mirroring the
  existing `authored_by` field on the decision side — to close part of the NEG-001 gap above.

## References

- **REF-001**: ADR-0001 — `docs/adr/ADR-0001-prd-adr-plan-runbook-methodology.md`
- **REF-002**: ADR-0020 — `itshaker-dgx-spark-V2/docs/adr/ADR-0020-hermes-builder-openhands-orchestration.md`
- **REF-003**: `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`
