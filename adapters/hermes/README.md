# adapters/hermes — Hermes-specific configuration (ADR-0007)

Projects are agent-neutral: they carry `AGENTS.md`, `CLAUDE.md`, `.ai/`, `.claude/`,
`scripts/orchestrate.py` and `docs/`. Everything here is specific to Hermes and is installed in
**Hermes' environment**, never in projects.

| Path | Installed as | Purpose |
|------|--------------|---------|
| `skills/sequential-coding-team/SKILL.md` | Hermes skill | Procedure: plan → task contracts → `orchestrate.py` → arbitration → human validation |
| `skills/sequential-coding-team/references/hermes-operating-rules.md` | installed with the skill | Role, gateway limits in tokens, `write_file` verification workaround, out-of-repo anchor, escalation — read by the skill when it runs |

## How Hermes loads context (verified on Arcane, HermesVPS2 ADR-0021)

- **`SOUL.md`** (`$HERMES_HOME/SOUL.md`, `/opt/data/SOUL.md` on Arcane) is the agent's
  **identity**: always loaded, in every session including chat. **Never overwrite or replace it.**
  It must not contain repository-specific paths. The only adapter content that belongs there is
  installation-wide facts, such as the current context window, maintained as a delimited section.
- **Project context**: Hermes loads **one** project file per session — `.hermes.md` / `HERMES.md`
  (searched upwards to the git root) **or** `AGENTS.md` (current directory only), with
  `.hermes.md` taking priority. A project that still has `.hermes.md` therefore hides its
  `AGENTS.md` from Hermes: delete obsolete `.hermes.md` files (ADR-0007).
- **Skills** are loaded on demand; their `references/` files are read when the skill asks.

## Install on Arcane (VPS2)

Workflows of `lowcodai/HermesVPS2` (self-hosted runner on VPS2):

- **Hermes Install Skill** — copies `skills/<skill>/` (with `references/`) into
  `hermes-gateway:/opt/data/skills/<category>/<skill>`, backs up the previous version outside
  the skills directory, verifies the copy.
- **Hermes SOUL Section** — shows, then (after human validation) updates one delimited section of
  `SOUL.md` (backup first, nothing outside the section is touched). Used for the context window.

## Other Hermes installations

Copy `skills/sequential-coding-team/` into the Hermes skills directory. Do not touch `SOUL.md`
beyond adding or updating a clearly delimited section by hand.

Another orchestrator? Add `adapters/<name>/` with its own skill; projects do not change.
