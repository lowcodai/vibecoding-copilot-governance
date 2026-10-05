# Audit — vibecoding-copilot-governance + vibecoding-bootstrap (2026-09-29)

Scope: both repos at `main` (`568cf78` governance, `15993d6` bootstrap), measured against the
target architecture "Hermes orchestrator + sequential Claude Code DEV / REVIEW / TEST" (ADR-0005)
on one `Qwen-3.8-27B-NVFP4` model served by vLLM on a DGX Spark, with one gateway per role:

| Gateway | Context | Output | Temp. |
|---|---:|---:|---:|
| Hermes orchestrator | 98k | 2k | 0.2 |
| Claude Code DEV | 98k | 4k | 0.2 |
| Claude Code REVIEW | 32k | 2k | 0.1 |
| Claude Code TEST | 32k | 2k | 0.1 |

Legend: **[fixed]** handled in this change set · **[open]** recommended follow-up.

## 1. Inconsistencies with the target architecture

| # | Finding | Where | Status |
|---|---|---|---|
| A1 | Hermes context documented as 65,536 tokens (thresholds, ADR density rules, runbook generator) — the gateway gives 98k with a 2k output cap, which nobody accounts for. | `hermes/.hermes.md`, `templates/ADR-template.md`, `agents/{adr,runbook}-generator.agent.md` | [fixed] |
| A2 | Mode A makes Hermes write code itself; the target says Hermes never codes. No independent review of code in Mode A. | methodology, ADR-0004 | [fixed] ADR-0005 narrows `hermes-solo` to docs/ops |
| A3 | Mode B = OpenHands app-conversations in parallel — a second agent runtime, never qualified outside one host, and parallelism is precisely what a single DGX Spark cannot afford. | methodology, ADR/RUNBOOK templates | [fixed] deprecated, replaced by `hermes-sequential-team` |
| A4 | No orchestration artefacts at all: no `.ai/orchestration.yaml`, task contract, state machine, run persistence, worktree policy, loop bounds or REVIEW/TEST verdict vocabulary. | — | [fixed] `dev-factory/` |
| A5 | Everything agent-facing is GitHub Copilot format (`.github/agents/*.agent.md`, Copilot `hooks.json` with `preToolUse`/`userPromptSubmitted`, `@agent` usage). Claude Code reads none of it: its hooks live in `.claude/settings.json` with a different payload (`tool_name`/`tool_input`). | `agents/`, `hooks/`, generated `AGENTS.md` | [fixed] Claude Code settings added; `tool-guardian` and `secrets-scanner` ported to Claude Code `PreToolUse` hooks (`.claude/hooks/`), active for DEV and interactive sessions |
| A6 | `AGENTS.md` is defined as "the list of Copilot agents" and generated as such; in the target it is the project rulebook every agent reads first. | `standards/documentation-standards.md`, `apply-template.sh` | [fixed] generated as a rulebook (commands, map, workflow, boundaries, DoD, per-type rules); standard updated |
| A7 | Several Copilot agents pin cloud models (`gpt-4o`, `GPT-4.1`, `GPT-5`, `Claude Sonnet 4.5`) — meaningless on a local-only stack. | `agents/agent-governance-reviewer`, `accessibility*`, `ai-readiness-reporter` | [open] |
| A8 | `ai-team-dev` ("Nova, Sage, Milo") tells the model to "make a reasonable decision" on ambiguity, push and open PRs, and reads `PROJECT_BRIEF.md` / sprint files that no template creates — contradicts ADR-0004's "never decide what the ADR left open" and ADR-0005's "never push". | `agents/ai-team-dev.agent.md` | [open] remove (superseded by the DEV role) |
| A9 | Instruction files are 600–870 lines each (a11y 731, docker 681, GH Actions 607, prompt safety 867). Any of them loaded into a 32k REVIEW/TEST window would consume a third of it. | `instructions/` | [open] keep for Copilot, never import into CLAUDE.md; distil 20-line checklists if needed |
| A10 | Branch model has no place for agent branches. | `standards/branching.md`, `naming-conventions.md` | [fixed] `agent/TASK-NNNN` |

## 2. Internal inconsistencies

| # | Finding | Where | Status |
|---|---|---|---|
| B1 | Two files numbered ADR-0004 (one accepted, one "superseded" draft with a different escalation list: $50 & 3 attempts vs €50 & 2 attempts, 5 vs 6 criteria). | `docs/adr/` | [fixed] draft moved to `docs/adr/withdrawn/`, status Withdrawn |
| B2 | ADR-0001 status "Superseded by ADR-0002" while ADR-0002 only supersedes its *language* clause — the methodology it created is still in force. It also cites `templates/*.fr.md` / `*.en.md` that no longer exist. | ADR-0001 | [fixed] status corrected, registry note |
| B3 | ADR-0003 `authored_by: frontier-model (Qwen3.8-27B-NVFP4)` — Qwen is the local model. Same ADR: "until the rename wave completes, then `vibecoding-copilot-governance`" (post-rename search/replace artefact). ADR-0004 still says "currently `itshaker-copilot-governance` on disk". | ADR-0003, ADR-0004 | [fixed] registry notes; ADR-0003 text rewritten by the rename tooling restored from `b3444d9` |
| B4 | The awesome-copilot map, `awesome-copilot-bundles.yml` and the hard-coded lists in `sync-governance.sh` disagree: `fix-broken-links` (map: base yes/infra no; script: base no/infra yes), `devops-core-principles` (map: base+infra; script: all types), `ai-team-dev` on m365 (map: no; script: yes), `containerization` on app (map: optional; script: mandatory), `ai-readiness-reporter` on m365 (map: default; bundle: optional), `prd-generator` absent from the map. | `docs/awesome-copilot-map.md`, bootstrap | [open] make the YAML the only source (see C2) and generate the map from it |
| B5 | m365 bundle references agents and instructions that do not exist in this repo (`declarative-agents-architect`, `mcp-m365-agent-expert`, `declarative-agents-microsoft365`, `mcp-m365-copilot`, `security-and-owasp`) — skipped silently. `session-auto-commit` hook is referenced in the map, bundles and two policies but does not exist. | bundles, map, policies | [open] |
| B6 | `tool-guardian/hooks.json` points to `hooks/tool-guardian/guard-tool.sh`; every other hook points to `.github/hooks/...`. After sync the tool guardian path is wrong, i.e. the one blocking hook never runs. | `hooks/tool-guardian/hooks.json` | [open] one-line fix if the Copilot layer is kept |
| B7 | README advertises `skills/`, `plugins/`, `scripts/sync-to-repo.sh` and BACKLOG/ROADMAP templates — none exist. | README | [fixed] |
| B8 | `config/templates.yml` is described as the source of truth for generated files, but no script reads it. It lists workflows that are never generated (`model-eval.yml`, `infrastructure-scan.yml`) and per-type `source_repo`s while `apply-template.sh` always copies `vibecoding-template-base`. | bootstrap `config/templates.yml`, `docs/design.md` | [open] wire it in or delete it |
| B9 | `sync-governance.sh` still accepts `--lang fr` although French generation is retired; `get_bundle_elements()` (the YAML reader) is never called; docs advertise `VIBECODING_GOVERNANCE_DIR` but the script reads `GOVERNANCE_DIR`. | bootstrap `scripts/sync-governance.sh`, `docs/usage.md` | [fixed] |
| B10 | Required status checks `ci` / `governance-check` in policies do not match the generated job names (`Check required files`, `Check for absence of secrets`); the generated check verifies 5 of the 10 "required" files. | `policies/branch-protection.md`, `standards/branching.md`, `apply-template.sh` | [open] |
| B11 | Commit conventions are specified twice with different type lists (`branching.md` has no `revert`/`security`). | `standards/` | [open] keep `commit-conventions.md` only |
| B12 | `adr-generator` produces `## Implementation Notes` with YAML front matter; `ADR-template.md` uses bold fields and `## Implementation`. Tools parsing ADRs must accept both. | agent vs template | [fixed] orchestrator matches by prefix; [open] converge on one format |

## 3. Useless or dead weight

| # | Item | Why | Status |
|---|---|---|---|
| C1 | `vibecoding-bootstrap/.agents/skills/` (344 KB, 20 skills) | Output of a `gh skills install` run inside the bootstrap repo, committed by accident; referenced by nothing. | [fixed] removed |
| C2 | `get_bundle_elements()` + the parallel hard-coded lists | Two sources of truth, one dead. | [fixed] dead function removed; [open] choose YAML-driven sync |
| C3 | `.hermes/plans/2026-09-14_...md` (750 lines, French) in the governance root | Historical session plan; any agent crawling the repo ingests it. | [open] move to `docs/history/` or out of the repo |
| C4 | Copilot-only surface for a Claude Code stack: `examples/copilot-instructions-*.md`, `acreadiness-*`, `arize-*`, `session-logger`, `governance-audit` prompt logging, the `m365` type | Not consumed by Hermes or Claude Code. | [open] decide: keep a Copilot "compat" layer, or remove (see §5) |
| C5 | `hermes/docs-adr-templates/README.md` pointing to `itshaker-dgx-spark-V2/docs/adr/README.md` for the ADR process | External, private reference; the process is in this repo. | [fixed] |
| C6 | `scripts/fetch-awesome-copilot.sh` sources the bootstrap libs through `../vibecoding-bootstrap` | Hidden cross-repo coupling. | [open] |

## 4. Target version (implemented)

```
vibecoding-copilot-governance/
├── docs/adr/ADR-0005-sequential-claude-code-team-orchestrated-by-hermes.md   (new)
├── dev-factory/                                                             (new)
│   ├── gateways.yaml                  gateway profiles + enforcement checklist
│   ├── hermes-skill/sequential-coding-team/SKILL.md
│   ├── project-template/              copied into each project by sync-governance.sh
│   │   ├── CLAUDE.md                  short; does not import AGENTS.md
│   │   ├── .claude/settings.json      deny push/merge/rebase/secrets/orchestrator files
│   │   ├── .ai/orchestration.yaml     agents, gateways, limits, validations, git policy
│   │   ├── .ai/tasks/TASK-template.md
│   │   ├── .ai/roles/{dev,review,test}.md
│   │   └── scripts/orchestrate.py     state machine (lock, worktree, budgets, persistence)
│   └── tests/test_orchestrate.py      12 tests, fake agent, no model needed
├── hermes/.hermes.md                  98k/2k thresholds, per-gateway note
├── templates/{ADR,RUNBOOK}-template.md   execution_mode: hermes-sequential-team | hermes-solo
└── docs/methodology/...WORKFLOW.md    Mode B replaced; Plan → Task (code) / Runbook (ops)

vibecoding-bootstrap/
└── scripts/sync-governance.sh         + sync_dev_factory, − dead code, − --lang fr
```

Key design decisions, driven by the model/gateway limits:

1. **Deterministic validation.** The orchestrator runs lint/tests; TEST (32k) interprets exit
   codes and log tails; a red command overrides any `PASS`.
2. **`--bare` for REVIEW/TEST.** Claude Code's own system prompt and tool schemas take a
   large share of 32k; `--bare` drops CLAUDE.md, memory and hooks, and `--tools` trims the tool
   list to `Read, Glob, Grep`.
3. **Explicit budgets.** `context − max_output − overhead_tokens` per role, head+tail truncation
   flagged in the work order; `usage` recorded in `timeline.log` for calibration.
4. **Output caps shape the protocol.** Role results are one compact JSON block; DEV edits in
   ≤ ~200-line chunks (4k); Hermes writes task contracts in two verified edits (2k).
5. **Gateway-enforced sampling.** Claude Code cannot set temperature; gateways pin temperature,
   clamp `max_tokens`, reject oversized prompts on 32k routes and disable Qwen thinking on 2k
   routes.
6. **Strictly sequential.** Repo-wide lock, `Task`/`Agent` tools disallowed, `max_num_seqs: 2`
   (Hermes idle + one Claude Code role).

## 5. Recommended next steps

1. ~~Accept or amend ADR-0005.~~ Accepted 2026-10-04. Next: run one real task and calibrate `overhead_tokens`.
2. Decide the fate of the Copilot layer (A5, A7–A9, C4): either a `compat/copilot/` folder that
   is no longer synced by default, or removal. Until then, nothing in it is loaded by Claude Code.
3. ~~Rewrite the generated `AGENTS.md` as the rulebook (A6).~~ Done. Correction (2026-10-04):
   the `vibecoding-template-*` repos had no `AGENTS.md` at all, and `apply-template.sh` never
   copies them (`apply_base_files()` is not called) — they are only consumed through GitHub's
   "Use this template". Each now carries the generator's rendering for its type, guarded by
   `vibecoding-bootstrap/tests/test-template-agents-md.sh`.
4. ~~Port `tool-guardian` and `secrets-scanner` to Claude Code hooks.~~ Done (`dev-factory/project-template/.claude/hooks/`).
5. ~~Clean the ADR ledger (B1–B3).~~ Done — see `docs/adr/README.md`.
6. Make `awesome-copilot-bundles.yml` the only source for sync (B4, B8) or delete the YAML.
