# adapters/hermes — Hermes-specific configuration (ADR-0007)

Projects are agent-neutral: they carry `AGENTS.md`, `CLAUDE.md`, `.ai/`, `.claude/`,
`scripts/orchestrate.py` and `docs/`. Everything below is specific to Hermes and is installed in
**Hermes' environment**, not in projects.

| File | Install as | Purpose |
|------|-----------|---------|
| `HERMES.md` | Hermes' global context (persistent instructions loaded in every session) | Role, gateway limits in tokens, `write_file` verification workaround, out-of-repo anchor, escalation |
| `skills/sequential-coding-team/` | Hermes' skills directory | Procedure: plan → task contracts → `orchestrate.py` → arbitration → human validation |

**Arcane (VPS2):** run the *Hermes Install Skill* workflow of `lowcodai/HermesVPS2`
(`.github/workflows/hermes-install-skill.yml`, self-hosted runner on VPS2). It copies
`skills/<skill>` into `hermes-gateway:/opt/data/skills/<category>/<skill>`, backs up the previous
version outside the skills directory and verifies the copy. `HERMES.md` is not installed by it.

Other installations:

```bash
# paths depend on the Hermes installation — adapt HERMES_HOME
cp -r adapters/hermes/skills/sequential-coding-team "$HERMES_HOME/skills/"
cp adapters/hermes/HERMES.md "$HERMES_HOME/<global-context-file>"
```

Hermes still reads each project's `AGENTS.md` first (the skill's step 1). A Hermes version that only
honours a per-project context file may use a local, **uncommitted** pointer to `AGENTS.md`
(ADR-0007, NEU-001).

Another orchestrator? Add `adapters/<name>/` with the same two pieces; projects do not change.
