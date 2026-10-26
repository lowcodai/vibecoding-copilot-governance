# adapters/openhands — OpenHands as a DEV executor (ADR-0010)

OpenHands is the second DEV executor of the orchestrated team, for **long sessions**. It is never
driven directly by an orchestrator agent on a governed repo: `scripts/orchestrate.py` runs it when a
task says `executor: openhands` and the repo allows it (`executors:` in `.ai/autonomy.yaml`).
REVIEW and TEST stay Claude Code.

## Runner contract (ADR-0010 DEC-004)

The machine or container where `orchestrate.py` runs OpenHands must guarantee:

1. the executor **and the validation commands** (they run the agent's code) run as an **unprivileged
   user**, distinct from the user running `orchestrate.py`: the runner sets
   `ORCHESTRATE_RUNNER_PREFIX` (or the repo sets `runner.prefix`) to the wrapper that drops to it, and
   installs the agent CLIs only on that user's `PATH`, so a run without the prefix fails closed;
2. **no container-runtime socket**, no `sudo`;
3. **no forge or git credentials** reachable by that user — the orchestrator pushes and opens PRs;
4. an environment **rebuilt from an allow-list**: the LLM route (`LLM_MODEL`, `LLM_BASE_URL`,
   `LLM_API_KEY`), `ORCHESTRATE_*`, locale and path — nothing else;
5. **no access to the orchestrator agent's data**: only the runner's own clones and worktrees; the
   agent user can write the task worktree and the repo's `.git`, and only read `.ai/`.

Network egress stays open (package registries, the LLM). With nothing to authenticate with, that is
the accepted residual risk; the orchestrator's gates (protected paths, `secrets-scan`, validations,
REVIEW, TEST) run before anything leaves the runner.

Reference implementation: `docker/dev-runner/` in `lowcodai/3m6-config` (Mac mini 3M6).

## Invocation

`orchestrate.py` writes the role prompt (`.ai/roles/dev-openhands.md`) and the work order to
`.ai/runs/<task>/dev-work-order.md` and runs, in the worktree:

```bash
<runner.prefix> openhands --headless --json --override-with-envs --exit-without-confirmation -f <work order>
```

with `LLM_MODEL` (LiteLLM slug, e.g. `openai/dgx-spark-current`), `LLM_BASE_URL` (OpenAI API,
`.../v1`) and `LLM_API_KEY` from the `oh-dev` gateway. The result is the last `FinishAction` message,
else the last agent `MessageEvent`, which must end with the DEV JSON block.

- Pin the CLI version in the runner (`uv tool install openhands==<version> --python 3.12`): its JSONL
  format changes between versions. Verified with OpenHands CLI 1.16.0.
- Headless OpenHands approves every action itself: isolation is the guard, not confirmation.
- Conversations accumulate under the agent user's `~/.openhands/conversations/`: prune them.

## Do not

- Use the generic Hermes `openhands` skill (CLI in the orchestrator's own container) on a governed repo.
- Give the agent user a GitHub token, an SSH key or a Docker socket "just for this task".
