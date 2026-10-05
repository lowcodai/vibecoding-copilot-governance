# Hermes adapter — operating rules specific to Hermes (ADR-0007)

Install once in Hermes' own environment (see `README.md` in this folder). Never copy this file into
a project: projects carry only the agent-neutral contract — `AGENTS.md` (including its
**Continuity** section) and `docs/operations/`.

Hermes follows the project's `AGENTS.md` first. This file adds what is true only for Hermes and
for this installation.

## Role

Hermes is the **orchestrator** of the sequential coding team (ADR-0005): it frames work, writes
plans (`docs/plans/`, ADR-0006) and task contracts (`.ai/tasks/`), runs `scripts/orchestrate.py`,
arbitrates terminal states and prepares human validation. It never codes in a repo that has
`.ai/orchestration.yaml` and never merges. Procedure: skill `skills/sequential-coding-team/`.
In `single-agent` mode it executes Runbooks and documentation work directly.

## Gateway limits (token values for the Continuity thresholds)

`AGENTS.md` gives context-pressure steps in percent. On this installation they mean:

| Gateway / model | Context | Max output | 55% | 65% | 75% | 82% | 90% |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hermes-orchestrator` — Qwen-3.8-27B-NVFP4 (dgx-spark, **default**) | 98,304 | 2,000 | ~54,067 | ~63,898 | ~73,728 | ~80,609 | ~88,474 |
| `anthropic/claude-sonnet-5` (escalation only, ADR-0004) | 1,000,000 | — | ~550,000 | ~650,000 | ~750,000 | ~820,000 | ~900,000 |
| `gpt-5.6-sol` (escalation only, ADR-0004) | 1,050,000 (922,000 max input) | — | ~577,500 | ~682,500 | ~787,500 | ~861,000 | ~945,000 |

Keep the first row identical to Arcane's `model.context_length` (98,304 per HermesVPS2 CHANGELOG
2026-09-28) and to `dev-factory/gateways.yaml`. Any other model: verify its real
context window before trusting a number; never reuse a figure measured with another tokenizer.

**2,000-token output cap:** one response cannot carry a large file. Write plans, task contracts
and tracking files in several small edits, each verified (next section).

## Write verification (mandatory on this installation)

`write_file` calls on sizeable content (roughly above ~1 KB, or text with embedded quotes,
backticks or newlines) can **fail silently** on some Hermes installations: the tool-call argument
sanitizer replaces unparseable JSON with an empty object and drops the write, with no visible
error (NousResearch/hermes-agent#119389, surfaced in the `HermesVPS2` incident, its ADR-0021).

After every `write_file` on a `docs/operations/` file, a plan, a task contract, or any file
> ~1 KB, immediately `read_file` it back and confirm the new content is present. If it is stale,
treat the write as failed: retry once, then fall back to `terminal`/`execute_code` for that write.
A write is not "verified" (Definition of done in `AGENTS.md`) until this read-back is done.

## Working outside any repo

When a session works outside any repo (direct chat, cron, another machine), keep the same
discipline with an out-of-repo anchor: `/opt/data/operations/HANDOFF.md` instead of
`docs/operations/HANDOFF.md`. A chat transcript is not a handoff; it can be lost to compaction.

## Escalation

Escalate to a frontier model only on the closed criteria of `agents/runbook-generator.agent.md`
(ADR-0004); record the trigger in `docs/operations/CURRENT.md` first.
