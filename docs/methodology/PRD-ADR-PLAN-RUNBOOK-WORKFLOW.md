> **Language of this corpus:** English is now the default language for all content in this
> governance repo and in every consumer repo (see ADR-0002). Documents *generated* in a target
> repo (PRD, ADR, `AGENTS.md`) are always written in English as well — there is no more per-repo
> language choice to check, and the decoupling rule this banner used to describe (superseded by
> ADR-0002) no longer applies.

# Methodology — PRD → ADR → Plan → Runbook / Task → Execution

## Why this chain

An agent that starts coding without a PRD or an ADR optimizes locally (the next file) with no
guarantee of global consistency (why, what architecture, what limits). This chain forces a
separation between **product intent** (PRD), **technical decision** (ADR), **executable
breakdown** (Plan), and **operational detail** (Runbook), so that an agent running local
inference (Qwen3.8-27B-NVFP4 on DGX Spark) can execute without having to arbitrate ambiguous
questions along the way — the arbitration has already happened, upstream, in the ADR.

## The chain

1. **PRD** (`docs/prd/PRD-NNNN-<slug>.md`, `templates/PRD-template.md`) — what/why, success
   criteria, non-goals. Zero implementation detail.
2. **ADR** (`docs/adr/ADR-NNNN-<slug>.md`, `templates/ADR-template.md`) — which technical
   decision, rejected alternatives, consequences, **and** the `execution_mode` field that locks
   in the chosen execution mode (see below).
3. **Plan** (`plan` / `writing-plans` skill, `.hermes/plans/*.md`) — breakdown into 2-5 minute
   tasks, exact file paths, complete code, verification commands. Created in plan mode by an
   agent (Hermes or GitHub Copilot).
4. **Runbook** (`docs/runbooks/RUNBOOK-NNNN-<slug>.md`, `templates/RUNBOOK-template.md`,
   `agents/runbook-generator.agent.md`) — sequenced operational detail, written before execution,
   never improvised during it. A Runbook must never introduce a decision absent from its linked
   ADR — if it encounters one, it stops and reports the gap instead of arbitrating it locally (see
   ADR-0004).
5. **Task contracts** (`.ai/tasks/TASK-NNNN.md`) for code, executed by the sequential Claude Code
   team — see §Execution modes and ADR-0005.

## Model tier recommendation (non-blocking)

- **PRD and ADR: a frontier model is strongly recommended** (Claude Sonnet 5, GPT-5.6 Sol, or
  equivalent) for irreversible, high-stakes decisions (public infrastructure, data, security,
  significant recurring cost).
- **A local model is allowed** (Qwen3.8-27B-NVFP4 / DGX Spark or equivalent) for cost reasons, in
  particular for reversible, low-stakes decisions, or fast iteration. A PRD/ADR with
  `authored_by: local-model` is a **valid, executable document** — it is never a tool or agent
  blocker, only an audit label. A frontier-model review is recommended before moving to
  "Accepted" status if the decision is high-stakes, but this remains a recommendation, not a
  blocking gate.
- The Plan and the Runbook do not carry this recommendation: they are execution artifacts, not
  decision artifacts.

## Default execution tier (Plan/Runbook/dev/test/security)

Per ADR-0004 (`docs/adr/ADR-0004-hermes-local-default-execution.md`), the model tier recommendation
above covers only PRD and ADR authoring. Downstream of an accepted ADR — Plan, Runbook,
development, test, and security work — the default executor is **Hermes running on the local
model** (`unsloth/Qwen3.8-27B-NVFP4`, DGX Spark, vLLM), taking on nearly all roles until an
operational, functional, iteratively-improvable solution is reached. Frontier-model execution
(Claude Sonnet 5, GPT-5.6 Sol) is the **exception**, triggered only by the closed criteria list
documented in `agents/runbook-generator.agent.md` (§Escalation Criteria) — not a default caution
reflex. That agent file is the single source of truth for the escalation criteria; this document
does not duplicate them.

The executor for **code** on the local model is the sequential Claude Code team (ADR-0005), not
Hermes itself; Hermes executes Runbooks (operations) and documentation work directly.

## Execution modes

### `hermes-sequential-team` — default for any change to code (ADR-0005)

Hermes is the Engineering Manager: it frames the work, writes one task contract per unit of work
(`.ai/tasks/TASK-NNNN.md`), runs `scripts/orchestrate.py`, arbitrates the outcome and prepares the
human validation. It does not code and never merges. The orchestrator runs one Claude Code role
at a time on one worktree per task:

```
PLANNED → DEV → REVIEW ─CHANGES_REQUESTED→ DEV
                  │
                  └→ TEST ─FAIL→ DEV
                       │
                       └→ READY_FOR_APPROVAL → human validation → merge (human)
```

| Role | Gateway | Context / output / temp. | Receives |
|---|---|---|---|
| Hermes | `hermes-orchestrator` | 98k / 2k / 0.2 | AGENTS.md, ADR, PRD, orchestration.yaml, TASK |
| DEV | `cc-dev` | 98k / 4k / 0.2 | TASK + feedback; reads AGENTS.md/ADR/PRD itself |
| REVIEW | `cc-review` | 32k / 2k / 0.1 | acceptance criteria, ADR Decision/Implementation, git diff |
| TEST | `cc-test` | 32k / 2k / 0.1 | acceptance criteria, validation exit codes + log tails |

Kit and details: `dev-factory/README.md`. Hermes procedure: skill `sequential-coding-team`.

### `hermes-solo` — documentation, governance, operations

A single Hermes agent executes the work directly: PRD/ADR drafting, governance edits, and
Runbook-driven operations (`docs/runbooks/`). No application code in this mode.

### `hermes-orchestrator-openhands` — deprecated

Superseded by ADR-0005 (never qualified outside `hermes-spark-builder`; parallel sandboxes do not
fit a single DGX Spark). Existing ADRs that name it keep their text; new ADRs must not use it.

## Where Plan, Runbook and Task fit

- **Plan** (`.hermes/plans/*.md`): Hermes' breakdown of an accepted ADR.
- **Task** (`.ai/tasks/TASK-NNNN.md`): one code unit of the Plan, executed by the Claude Code team.
- **Runbook** (`docs/runbooks/`): one operational unit of the Plan, executed by Hermes.

## References

- `templates/PRD-template.md`, `templates/ADR-template.md`, `templates/RUNBOOK-template.md`
- `agents/prd-generator.agent.md`, `agents/adr-generator.agent.md`,
  `agents/runbook-generator.agent.md`
- `dev-factory/` — orchestration kit (ADR-0005)
- ADR-0004 — `docs/adr/ADR-0004-hermes-local-default-execution.md` (local model by default)
- ADR-0005 — `docs/adr/ADR-0005-sequential-claude-code-team-orchestrated-by-hermes.md`
