# dev-factory — sequential Claude Code team and agent-neutral project kit

The kit in `project-template/` is agent-neutral (ADR-0007): any orchestrator can drive it.
Hermes is today's orchestrator; its specific rules and skill are in `adapters/hermes/`.

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
        READY_FOR_APPROVAL ─► human validation ─► merge (human, or the orchestrator at `trusted`)
```

How far agents may go (push, merge, curl/wget, gh) is a per-repo **autonomy level** declared in
`.ai/autonomy.yaml` (ADR-0008, proposed): `supervised` (default), `branch` or `trusted`.

## Contents

| Path | Copied to project as | Purpose |
|---|---|---|
| `project-template/.ai/orchestration.yaml` | `.ai/orchestration.yaml` | agents, gateways, transitions limits, validation commands, git policy |
| `project-template/.ai/autonomy.yaml` | `.ai/autonomy.yaml` | autonomy level of the repo (human-owned, protected; ADR-0008) |
| `project-template/.ai/tasks/TASK-template.md` | `.ai/tasks/TASK-template.md` | task contract skeleton (`orchestrate.py new`) |
| `project-template/.ai/roles/*.md` | `.ai/roles/*.md` | role prompts + JSON result contracts |
| `project-template/.claude/settings.json` | `.claude/settings.json` | deny rules + hook wiring — **generated** from the level by `autonomy.py render` |
| `project-template/.claude/hooks/autonomy.py` | `.claude/hooks/autonomy.py` | the only policy definition: levels, effective level, `render`, `check` |
| `project-template/.claude/hooks/tool_guardian.py` | `.claude/hooks/tool_guardian.py` | PreToolUse (Bash): blocks destructive, exfiltrating or policy-breaking commands |
| `project-template/.claude/hooks/secrets_scanner.py` | `.claude/hooks/secrets_scanner.py` | PreToolUse (Write/Edit, `git commit`) + `--range` CLI used as a validation |
| `project-template/.claude/hooks/secrets-allowlist.txt` | `.claude/hooks/secrets-allowlist.txt` | human-owned path/pattern exceptions for the scanner |
| `project-template/CLAUDE.md` | `CLAUDE.md` | short project memory for interactive sessions and DEV (one generated autonomy line) |
| `project-template/scripts/orchestrate.py` | `scripts/orchestrate.py` | the state machine |
| `gateways.yaml` | — (infra reference) | gateway profiles + enforcement checklist |
| `project-template/docs/` | `docs/{prd,adr,plans,runbooks,operations}/` | agent-neutral docs skeleton (ADR-0007) |
| `tests/` | — | `python3 -m unittest discover -s dev-factory/tests` |

`vibecoding-bootstrap/scripts/sync-governance.sh` copies `project-template/` into projects. Kit-owned
files (`.claude/settings.json`, `.claude/hooks/*.py`, `scripts/orchestrate.py`) are refreshed on every
sync; project-tuned files (`.ai/orchestration.yaml`, `.ai/roles/`, `CLAUDE.md` outside its autonomy
block, the secrets allowlist, `docs/`) are never overwritten (ADR-0008 DEC-007).

## Run a task

```bash
python3 scripts/orchestrate.py new TASK-0042 --title "Add JWT refresh"
# Hermes fills .ai/tasks/TASK-0042.md (objective, scope, ACs, adrs, validations)
python3 scripts/orchestrate.py run TASK-0042      # start or resume; exit 0 = READY, 2 = BLOCKED
python3 scripts/orchestrate.py status TASK-0042
python3 scripts/orchestrate.py approve TASK-0042 --by "Jeremie"    # then merge agent/TASK-0042 (merged for you at `trusted`)
python3 scripts/orchestrate.py rework TASK-0042 --feedback "..."   # human sends it back to DEV
```

Per run, `.ai/runs/TASK-0042/` holds `state.json`, `{dev,review,test}-result.json`,
`*-work-order.md`, `*-raw-output.txt`, `validations.json`, `logs/*.log`, `timeline.log`.

## Autonomy levels (ADR-0008, proposed)

The level lives in `.ai/autonomy.yaml`. The **effective** level is the most restrictive of that file
and its copy on the base branch: raising it only works once a human has merged the change; a missing
or invalid file means `supervised`. No environment variable is consulted.

| Action | `supervised` | `branch` | `trusted` |
|---|---|---|---|
| Push (interactive) | no | current non-`main` branch only: `git push -u origin <branch>` | same |
| Push + draft PR (orchestrated) | no | orchestrator, at `READY_FOR_APPROVAL` | same |
| Merge (interactive) | no | `main` into one's own branch | + own PR when all checks are green |
| Merge (orchestrated) | human | human | orchestrator, after `orchestrate.py approve`, checks green |
| curl / wget | no | yes (no pipe to a shell, no upload) | yes |
| gh | no | read-only, `pr create --draft`, `pr comment` (DEV: read-only) | + `pr merge` of own green PR |

At every level: no force push, no push to / commit on / merge into `main`, no tag push, no `rebase`,
no `git pull`, no `--no-verify`, no push redirection (`remote.*.push`, `url.*.insteadOf`,
`core.hooksPath`, `git -c`), no secrets read or committed, no protected-path change, no `sudo`,
no exfiltration, no publication. DEV never pushes or merges itself, at any level.

Change a repo's level with `vibecoding-bootstrap/scripts/sync-governance.sh --autonomy <level>`, then
review and merge the diff. `autonomy.py check` (built into every orchestrated run as the
`autonomy-check` validation) fails when a generated file no longer matches the level.

**No branch protection, no server-side backstop.** At `branch` and `trusted`, enable branch
protection on `main` where the GitHub plan allows it (`policies/branch-protection.md`); private repos
on a Free plan cannot, and then the hook's narrow push allow-list is the only barrier.

## Guard rails: hooks, deny rules, deterministic scan

| Layer | Applies to | Enforced by | Depends on the level |
|---|---|---|---|
| `--tools` list | every role | Claude Code (REVIEW/TEST only have Read, Glob, Grep) | no |
| Deny rules (`.claude/settings.json`) | DEV + interactive sessions (REVIEW/TEST via `--settings`) | Claude Code permissions | yes — rendered by `autonomy.py` |
| `tool_guardian.py` (PreToolUse, Bash) | DEV + interactive sessions | hook, exit 2 blocks, fail-closed | yes — reads the effective level |
| `secrets_scanner.py` (PreToolUse, Write/Edit and `git commit`) | DEV + interactive sessions | hook, exit 2 blocks, fail-closed | no |
| `disallowed_tools` | every role | orchestrator (`Task`, `Agent`; `WebFetch`, `WebSearch` at `supervised`) | yes |
| `autonomy-check` validation | every task, before TEST | orchestrator — generated files match the level | — |
| `secrets-scan` validation (`--range base..HEAD`) | every task, before TEST | orchestrator — independent of hooks | no |
| Protected paths (`git.protected_paths` + the policy's own list) | every task, after DEV | orchestrator — a diff touching `.claude/`, `.ai/autonomy.yaml`, `.ai/orchestration.yaml`, `.ai/roles/` or `orchestrate.py` goes back to DEV | no |
| Push, PR, merge | orchestrated tasks | orchestrator — deterministic, never an agent | yes |

Known false positives of the scanner go in `.claude/hooks/secrets-allowlist.txt`
(`<path glob> <PATTERN,...>` per line). It ships with the documentation examples of the Copilot
`secrets-scanner` hook. Agents cannot change it: deny rules, `tool_guardian` (shell writes to
`.claude/`) and the protected-paths guard all stand in the way — only humans edit it, in a PR.

DEV runs without `--bare` (with `--setting-sources project`) precisely so the hooks run; the
orchestrator refuses to start DEV (`BLOCKED`) if `.claude/settings.json` or the hook scripts are
not committed on the base branch. Hook logs go to `.ai/runs/<task>/hooks/*.jsonl` during
orchestrated runs (`CLAUDE_HOOK_LOG_DIR`), `~/.local/state/claude-hooks/<project>/` otherwise —
never inside the worktree, which must stay clean. Overrides (`GUARD_MODE`, `TOOL_GUARD_ALLOWLIST`,
`SECRETS_ALLOWLIST`, `SECRETS_BLOCK_SEVERITY`, `SKIP_*`) are environment variables set by humans; none
of them can raise the autonomy level.

## Design choices that matter on a 27B local model

- **Validation is deterministic.** The orchestrator runs lint/test commands itself; TEST only
  interprets them, and a red command can never become `PASS`.
- **REVIEW/TEST run with `--bare`, DEV does not.** Without it, Claude Code auto-loads CLAUDE.md, memory and
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
