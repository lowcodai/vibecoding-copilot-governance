# dev-factory — sequential Claude Code team orchestrated by Hermes

Implements ADR-0005. One model (`Qwen-3.8-27B-NVFP4`, vLLM on DGX Spark), one gateway per
role, one Claude Code role active at a time.

```
User ─► Hermes (Engineering Manager, gateway hermes-orchestrator 98k/2k/0.2)
          │  reads AGENTS.md, ADR, PRD, .ai/orchestration.yaml; writes .ai/tasks/TASK-NNNN.md
          ▼
        scripts/orchestrate.py  (state machine, lock, worktree, persistence)
          ├─► Claude Code DEV     (cc-dev     98k / 4k / 0.2)  edits + local commits
          ├─► Claude Code REVIEW  (cc-review  32k / 2k / 0.1)  diff + ACs + ADR excerpts
          └─► Claude Code TEST    (cc-test    32k / 2k / 0.1)  validation results
          ▼
        READY_FOR_APPROVAL ─► human validation ─► merge (human)
```

## Contents

| Path | Copied to project as | Purpose |
|---|---|---|
| `project-template/.ai/orchestration.yaml` | `.ai/orchestration.yaml` | agents, gateways, transitions limits, validation commands, git policy |
| `project-template/.ai/tasks/TASK-template.md` | `.ai/tasks/TASK-template.md` | task contract skeleton (`orchestrate.py new`) |
| `project-template/.ai/roles/*.md` | `.ai/roles/*.md` | role prompts + JSON result contracts |
| `project-template/.claude/settings.json` | `.claude/settings.json` | deny rules (push/merge/rebase, secrets, orchestrator files) |
| `project-template/CLAUDE.md` | `CLAUDE.md` | short project memory for interactive sessions |
| `project-template/scripts/orchestrate.py` | `scripts/orchestrate.py` | the state machine |
| `gateways.yaml` | — (infra reference) | gateway profiles + enforcement checklist |
| `hermes-skill/sequential-coding-team/` | Hermes skills dir | Hermes procedure |
| `tests/` | — | `python3 -m unittest discover -s dev-factory/tests` |

`vibecoding-bootstrap/scripts/sync-governance.sh` copies `project-template/` into projects
(never overwriting an existing file).

## Run a task

```bash
python3 scripts/orchestrate.py new TASK-0042 --title "Add JWT refresh"
# Hermes fills .ai/tasks/TASK-0042.md (objective, scope, ACs, adrs, validations)
python3 scripts/orchestrate.py run TASK-0042      # start or resume; exit 0 = READY, 2 = BLOCKED
python3 scripts/orchestrate.py status TASK-0042
python3 scripts/orchestrate.py approve TASK-0042 --by "Jeremie"    # then merge agent/TASK-0042
python3 scripts/orchestrate.py rework TASK-0042 --feedback "..."   # human sends it back to DEV
```

Per run, `.ai/runs/TASK-0042/` holds `state.json`, `{dev,review,test}-result.json`,
`*-work-order.md`, `*-raw-output.txt`, `validations.json`, `logs/*.log`, `timeline.log`.

## Design choices that matter on a 27B local model

- **Validation is deterministic.** The orchestrator runs lint/test commands itself; TEST only
  interprets them, and a red command can never become `PASS`.
- **REVIEW/TEST run with `--bare`.** Without it, Claude Code auto-loads CLAUDE.md, memory and
  hooks into a 32k window. Their context is assembled by the orchestrator (head+tail truncation
  when needed, flagged in the work order).
- **CLAUDE.md does not import AGENTS.md.** Imports are loaded into every session; DEV reads
  AGENTS.md explicitly instead.
- **No sub-agents.** `Task`/`Agent` tools are disallowed to keep one active agent.
- **Output caps shape the prompts.** DEV (4k) edits in small chunks; REVIEW/TEST (2k) return a
  compact JSON block; Hermes (2k) writes task contracts in two verified edits.
- **Temperature and thinking are gateway settings.** Claude Code cannot set temperature; disable
  Qwen thinking on 2k-output routes or reasoning tokens will crowd out the answer.

## Calibrate before trusting the budgets

1. Run one small task end to end.
2. Read the `usage` lines in `timeline.log` (input tokens per role).
3. Set `agents.<role>.overhead_tokens` in `.ai/orchestration.yaml` to the observed input tokens
   of a near-empty work order, plus a 10% margin.

## Gateway example (LiteLLM, one route per role)

```yaml
model_list:
  - model_name: qwen3.8-27b-nvfp4          # route used with the cc-review key
    litellm_params:
      model: hosted_vllm/qwen3.8-27b-nvfp4
      api_base: http://127.0.0.1:8000/v1
      temperature: 0.1
      max_tokens: 2000
      extra_body: {chat_template_kwargs: {enable_thinking: false}}
```

Adapt to your proxy: what matters is the enforcement checklist at the end of `gateways.yaml`.
