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
**execution_mode:** hermes-sequential-team | hermes-solo
<!-- hermes-sequential-team (default for any decision that changes code, ADR-0005): Hermes
     orchestrates, Claude Code DEV → REVIEW → TEST run one at a time via scripts/orchestrate.py,
     a human validates and merges.
     hermes-solo: Hermes alone, for documentation, governance and Runbook-driven operations
     (no application code).
     hermes-orchestrator-openhands is deprecated (ADR-0005) — do not use it in new ADRs.
     Selection criteria: see docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md §Execution modes.
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

     Density rule (local-model execution, the default per ADR-0004): REVIEW only receives the
     Decision and Implementation sections of each linked ADR, inside a 32k-token budget shared
     with the diff (ADR-0005); DEV and Hermes work within 98k. Context/Decision/Implementation
     must therefore use coded bullets rather than free prose, and Decision + Implementation
     together should stay under ~1,000 words so they fit next to a typical diff. -->

## References

- [Documentation link]()
- [Related ADRs](./ADR-XXXX.md)
```
