# Naming Conventions — vibecoding

## Repositories

| Pattern | Example | Usage |
|---------|---------|-------|
| `vibecoding-template-<type>` | `vibecoding-template-base` | GitHub templates |
| `vibecoding-<function>` | `vibecoding-bootstrap` | Internal tools |
| `<project>-<stack>` | `my-api-node`, `my-infra-aws` | Business projects |

## Branches

| Pattern | Example | Usage |
|---------|---------|-------|
| `main` | `main` | Main branch (protected) |
| `feat/<slug>` | `feat/add-user-auth` | New features |
| `fix/<slug>` | `fix/login-crash` | Bug fixes |
| `chore/<slug>` | `chore/update-deps` | Maintenance |
| `docs/<slug>` | `docs/update-api-spec` | Documentation |
| `hotfix/<slug>` | `hotfix/critical-security` | Urgent fixes |
| `agent/TASK-NNNN` | `agent/TASK-0042` | Sequential Claude Code team — one task, one branch, one worktree (ADR-0005). Created by `scripts/orchestrate.py` only |

## Files and directories

- **Files**: `kebab-case` for Markdown and config files, `snake_case` for shell scripts
- **Directories**: `kebab-case` (e.g. `docs/adr/`, `my-module/`)
- **Secrets**: never in file names, never committed

## Environment variables

- `SCREAMING_SNAKE_CASE` (e.g. `DATABASE_URL`, `API_KEY`)
- Prefixed by domain: `GITHUB_*`, `APP_*`, `AWS_*`

## GitHub Labels

See `config/labels.yml` in vibecoding-bootstrap.

Format: `<category>: <value>` (e.g. `type: bug`, `priority: high`)
