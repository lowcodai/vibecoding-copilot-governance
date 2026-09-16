# ADR template

```markdown
# ADR-XXXX — Decision title

**Date:** YYYY-MM-DD
**Status:** Proposed | In progress | Accepted | Rejected | Deprecated | Superseded by ADR-YYYY
**Decision makers:** <!-- Names or roles -->
**Technical context:** <!-- Stack, version, etc. -->
**authored_by:** frontier-model (recommended) | local-model
<!-- See PRD-template.md for the definition. A local-model ADR remains valid; document the
     choice for audit purposes and to flag that a frontier-model review is recommended before
     "Accepted" if the decision is irreversible or high-stakes (public infra, data, significant
     recurring cost). -->
**execution_mode:** hermes-solo | hermes-orchestrator-openhands
<!-- hermes-solo: a single Hermes agent sequentially takes on every role (architect/dev/
     tester/security/ops) within its own context — via subagent-driven-development.
     hermes-orchestrator-openhands: Hermes only plays the Orchestrator role and delegates each
     role to an isolated OpenHands app-conversation (separate sandbox + repo/branch) — pattern
     accepted by ADR-0020 (itshaker-dgx-spark-V2), driven via oh_pilot.py / skill openhands-pilot.
     Selection criteria: see docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md §Modes.
     Per ADR-0004, the model tier executing the Plan/Runbook downstream of either mode defaults to
     Hermes-on-local; frontier-model execution is the exception, on the criteria documented in
     agents/runbook-generator.agent.md — this field is about role isolation, not model tier. -->

## Context

<!-- Describe the situation, problem, or need driving this decision.
     Include the constraints and forces at play. -->

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Option A | ... | ... |
| Option B | ... | ... |
| Option C | ... | ... |

## Decision

<!-- The decision made and its justification.
     Format: "We choose **Option X** because..." -->

## Consequences

### Positive
- ...

### Negative
- ...

### Neutral / To monitor
- ...

## Implementation

<!-- MANDATORY execution contract — never "if applicable", never left empty for a decision that
     changes code, config, or infrastructure. This section must be sufficient for a Plan and then
     a Runbook (see templates/RUNBOOK-template.md) to be generalized by a local-model executor
     (see ADR-0004, docs/adr/ADR-0004-hermes-local-default-execution.md) WITHOUT re-arbitrating
     architecture. It must state, explicitly:
     - Exact file paths to be created or modified (not "the relevant service files").
     - Interfaces / data contracts: function signatures, schemas, request/response shapes, or
       message formats crossed by this decision.
     - Error behavior: what happens when a precondition of this decision fails at runtime.
     - Rollback condition: the exact trigger and action to undo this decision if it goes wrong.
     Use coded bullets (IMP-001, IMP-002, ...) for each point — see agents/adr-generator.agent.md.

     Density rule when execution_mode targets Hermes-on-local (hermes-solo or
     hermes-orchestrator-openhands with a local-model executor): the local model's context window
     is bounded (65,536 tokens for unsloth/Qwen3.8-27B-NVFP4 — see hermes/.hermes.md). In that
     case, Context/Decision/Implementation must use coded bullets rather than free prose, and the
     whole ADR should stay within an indicative ~2,000 words / ~400 lines so it remains
     self-sufficient without forcing a reload of the full linked PRD into working context. -->

## References

- [Documentation link]()
- [Related ADRs](./ADR-XXXX.md)
```
