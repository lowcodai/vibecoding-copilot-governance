# vibecoding-copilot-governance

> Central governance repository — shared standards, instructions, hooks, policies, agents, and Awesome Copilot references for all lowcodai projects.

## Role

This repository is the **single source of truth** for:
- Development and documentation standards
- Shared Copilot instructions
- Security and governance hooks
- Recommended agents and skills
- Policies (licenses, secrets, branching)
- PRD, ADR, PLAN, RUNBOOK, ISSUE_TEMPLATE, PR_TEMPLATE templates
- The sequential Claude Code team kit (`dev-factory/`, ADR-0005)

## Structure

```
vibecoding-copilot-governance/
├── standards/          ← Conventions (branching, commits, PR, naming, documentation)
├── policies/           ← Policies: AI usage, secrets, licenses, branch protection
├── templates/          ← PRD, ADR, PLAN, RUNBOOK, ISSUE_TEMPLATE, PR_TEMPLATE
├── docs/               ← ADRs, methodology, audits, awesome-copilot map
├── dev-factory/        ← Agent-neutral project kit: orchestrate.py, .ai/, .claude/, docs/ skeleton (ADR-0005/0007)
├── adapters/hermes/    ← Hermes-specific rules and skill, installed in Hermes' environment (ADR-0007)
├── agents/             ← .agent.md files (GitHub Copilot format)
├── instructions/       ← .instructions.md files sourced from github/awesome-copilot
├── hooks/              ← GitHub Copilot hooks (tool-guardian, secrets-scanner, ...)
├── scripts/            ← fetch-awesome-copilot.sh
└── examples/           ← Example copilot-instructions.md files by project type
```

Skills and plugins are not stored here: they are installed in the target environment
(`gh skills install`, `copilot plugin install`).

## Dev factory (`dev-factory/`)

Code work runs as a sequential team — Hermes orchestrates, Claude Code DEV → REVIEW → TEST run
one at a time on the local model through dedicated gateways, a human validates and merges.
See ADR-0005 and [dev-factory/README.md](dev-factory/README.md).

## Project contract vs. agent adapters (ADR-0007)

Projects are **agent-neutral**: they receive `AGENTS.md` (with its Continuity section),
`CLAUDE.md`, `.ai/`, `.claude/`, `scripts/orchestrate.py` and the `docs/` skeleton
(`prd/`, `adr/`, `plans/`, `runbooks/`, `operations/`) from `dev-factory/project-template/`.
Rules specific to an orchestrator live in `adapters/<agent>/` and are installed in that agent's
environment — today [`adapters/hermes/`](adapters/hermes/README.md). No `.hermes.md` is shipped to
projects anymore.

## Usage

### Sync governance into an existing project

```bash
# From vibecoding-bootstrap
./scripts/sync-governance.sh --type <base|infra|ai|app|m365> --dest /path/to/project
```

### Update awesome-copilot elements

```bash
./scripts/install-awesome-copilot.sh --type <type> --dest /path/to/project
```

## Source of Copilot elements

- **Repository:** [github/awesome-copilot](https://github.com/github/awesome-copilot)
- **Reference SHA:** `dae77f24132c1d686c30fd5b29aee0d63668d1d2`
- **Skill installation:** `gh skills install github/awesome-copilot <skill-name>` (gh CLI v2.90.0+)
- **Plugin installation:** `copilot plugin install <name>@awesome-copilot`
- **`instructions/`, `hooks/`, `agents/` populated on 2026-09-14** from this SHA (fix: these
  folders were referenced by `sync-governance.sh` but absent from the repo — the script ran
  silently as a no-op, `log_warn` without failure). `skills/` and `plugins/` remain
  deliberately empty: installed via `gh skills install` / `copilot plugin install` directly in
  the target environment, not copied as files into this repo.

## Distribution matrix by project type

See [docs/awesome-copilot-map.md](docs/awesome-copilot-map.md)

## Updating

When this repository is updated, rerun `sync-governance.sh` in the affected projects to propagate the changes.

```bash
# Update a project
cd /path/to/vibecoding-bootstrap
./scripts/sync-governance.sh --type infra --dest /path/to/my-project --extend-only
```
