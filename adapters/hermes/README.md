# adapters/hermes — Hermes-specific configuration (ADR-0007)

Projects are agent-neutral: they carry `AGENTS.md`, `CLAUDE.md`, `.ai/`, `.claude/`,
`scripts/orchestrate.py` and `docs/`. Everything here is specific to Hermes and is installed in
**Hermes' environment**, never in projects.

| Path | Installed as | Purpose |
|------|--------------|---------|
| `skills/sequential-coding-team/SKILL.md` | Hermes skill | Procedure: plan → task contracts → `orchestrate.py` → arbitration → human validation |
| `skills/sequential-coding-team/references/hermes-operating-rules.md` | installed with the skill | Role, gateway limits in tokens, `write_file` verification workaround, out-of-repo anchor, escalation — read by the skill when it runs |

## How Hermes loads context (verified on Arcane)

- **`SOUL.md`** (`$HERMES_HOME/SOUL.md`, `/opt/data/SOUL.md` on Arcane) is the agent's
  **identity**: always loaded, in every session including chat. **Never overwrite or replace it.**
  It must not contain repository-specific paths. The only adapter content that belongs there is
  installation-wide facts, such as the current context window, maintained as a delimited section.
- **Project context**: Hermes loads **one** project file per session — `.hermes.md` / `HERMES.md`
  (searched upwards to the git root) **or** `AGENTS.md` (current directory only), with
  `.hermes.md` taking priority. A project that still has `.hermes.md` therefore hides its
  `AGENTS.md` from Hermes: delete obsolete `.hermes.md` files (ADR-0007).
- **Skills** are loaded on demand; their `references/` files are read when the skill asks.

## Install on Arcane (3M6)

Arcane runs on the Mac mini 3M6 (`3m6.home`), deployed from `lowcodai/arcane3m6`: container
`hermes-gateway`, data volume `arcane-data` mounted at `/opt/data`, skills under
`/opt/data/skills/<category>/<skill>`. There is no self-hosted runner there, and by that repo's
ADR-0001 D-4 nobody edits Arcane's skills or `SOUL.md` by hand: **Arcane is sent a short brief and
updates them itself**, then reports what it changed.

- **Skill** — brief Arcane to install or update `skills/sequential-coding-team/` (with
  `references/`) from this repository's `main`, keeping a copy of the previous version outside the
  skills directory, and to confirm with `hermes skills list`. The current brief is
  `docs/arcane-skill-sequential-coding-team-brief.md` in `lowcodai/arcane3m6`.
- **`SOUL.md`** — only the delimited context-window section (`<!-- BEGIN/END managed-section:
  context-window -->`) is ever changed, by Arcane, on a brief that gives the new figures.

## Other Hermes installations

Copy `skills/sequential-coding-team/` into the Hermes skills directory. Do not touch `SOUL.md`
beyond adding or updating a clearly delimited section by hand.

Another orchestrator? Add `adapters/<name>/` with its own skill; projects do not change.
