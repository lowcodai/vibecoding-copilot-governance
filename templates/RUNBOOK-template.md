# Runbook template

```markdown
# RUNBOOK-NNNN — Operation title

**Date:** YYYY-MM-DD
**Status:** Draft | Ready | In progress | Done | Aborted
**linked_adr:** ADR-XXXX
<!-- MANDATORY, never empty, never "N/A" and never "TBD". A Runbook that has no linked_adr
     documents no decision-making authority of its own — see ADR-0004
     (docs/adr/ADR-0004-hermes-local-default-execution.md). If no ADR exists yet for this
     operation, stop here and create one first (agents/adr-generator.agent.md) — do not start
     a Runbook to work around a missing decision. -->
**authored_by:** frontier-model | local-model
**execution_mode:** hermes-solo | hermes-orchestrator-openhands
<!-- Inherited verbatim from linked_adr's execution_mode field — a Runbook never chooses its own
     execution_mode independently of the ADR that authorizes it. -->

## Preconditions

<!-- State required before starting, each one independently checkable — not "the environment is
     ready" but the literal command that proves it. Example:
     - Branch `feature/x` exists and is checked out: `git branch --show-current` returns `feature/x`.
     - Required env var is set: `test -n "$VAR_NAME"` exits 0.
     - Dependency service is reachable: `curl -sf https://internal-service/health` returns 200. -->

## Steps

<!-- Numbered, sequential, no free prose outside a step. Each step is:
     1. A short, unambiguous title.
     2. The exact command(s) to run — copy-pasteable, no placeholders left for the executor to
        fill in from judgment (resolve every placeholder before handing off the Runbook).
     3. An exact verification command and its expected result — never "check that it works."
     4. For any step marked at-risk: an explicit rollback condition (the command or action that
        undoes this step, and the exact signal that triggers it).

     Example:

     ### Step 1 — <title>

     Command:
     ```bash
     <exact command>
     ```

     Verify:
     ```bash
     <exact verification command>
     ```
     Expected: <exact expected output or state>

     Rollback condition (if at-risk): <exact trigger> → <exact rollback command> -->

## Escalation stop condition

<!-- Mandatory, verbatim intent (adapt wording, not substance):

     "If any step in this Runbook requires a decision not already made in `linked_adr`, STOP.
     Do not decide it locally, do not infer it from surrounding code or convention. Record the
     exact gap in `docs/operations/CURRENT.md`, then escalate per the criteria documented in
     `agents/runbook-generator.agent.md`."

     This is the guard-rail that lets a bounded-context local model (see hermes/.hermes.md)
     execute this Runbook unattended without re-arbitrating architecture. A Runbook is not the
     place to fill an ADR's gaps — it is the place that proves the gap exists. -->

## Definition of Done

<!-- Mirrors the continuity contract in hermes/.hermes.md — a step is not done until:
     1. Its verification command has actually been run (real output, not assumed).
     2. `docs/operations/CURRENT.md` reflects the new state.
     3. `CHANGELOG.md` is updated if the change is user-visible, architectural, or operational.
     4. Modified files and any unresolved risk are recorded.
     5. The next executable action (or "none — operation complete") is recorded. -->

## References

- Linked ADR: `docs/adr/ADR-XXXX-<slug>.md`
- Source Plan: <!-- path to the .hermes/plans/*.md this Runbook was generated from, if any -->
```
