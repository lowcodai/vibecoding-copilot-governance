# ADR-0003 — Rename the family prefix `itshaker` to `vibecoding`

**Date:** 2026-09-15
**Status:** Accepted
**Decision-makers:** Capitaine (Jérémie Coste) — full execution approved (autopilot)
**Technical context:** lowcodai governance ecosystem (templates, Copilot agents, methodology) — repo `itshaker-copilot-governance` (until the rename wave completes, then `vibecoding-copilot-governance`).
**authored_by:** frontier-model (Qwen3.8-27B-NVFP4)
**execution_mode:** hermes-solo

> **Registry note (2026-09-29):** (1) The rename wave's own content replacement (commit `9535d88`)
> rewrote the *old* names in this ADR, making it read "rename `vibecoding-*` to `vibecoding-*`".
> The technical context, the Context paragraph, the allowlist entries and the env var names are
> restored verbatim from the authored version (`b3444d9`); repo paths used as links keep the new
> names. (2) `authored_by` is contradictory as authored: Qwen3.8-27B-NVFP4 is the local model —
> read it as `local-model`. (3) Since 2026-09-29 `VIBECODING_GOVERNANCE_DIR` *is* read by
> `vibecoding-bootstrap/scripts/sync-governance.sh`; the "not read by any script" statement
> below describes 2026-09-15.

## Context

The template family — four template repos (`itshaker-template-base`,
`itshaker-template-infra`, `itshaker-template-ai`, `itshaker-template-app`),
the instantiation engine (`itshaker-bootstrap`) and this governance repo
(`itshaker-copilot-governance`) — predate the `vibecoding` naming the user now
prefers for the template/governance product line. The user requested
(2026-09-15): replace the `itshaker` prefix with `vibecoding` across the six
repos.

Business projects (`itshaker-dgx-spark-V2`, `ITShaker-llmwiki`) are **not**
part of this rename. Every historical reference to them inside the six repos
is a traceability record (e.g. ADR-0001 cites the `itshaker-dgx-spark-V2`
ADR-0020 chain as its pattern source) and must survive the change intact.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Re-create the six repos under the new names (new git history) | Clean break | Full history, issues, template flags, stars lost; every consumer (clones, skills, runbooks, past commits in other repos) hard-breaks |
| In-place rename via GitHub API (`PATCH /repos/{owner}/{repo}`, `new_name`) | History, branches, issues, template flags and stars preserved; GitHub 301-redirects every old URL (clone/web/API); zero forks on all six repos (verified 2026-09-15) | Public repos — the rename is visible in shared clone URLs (mitigated by redirects) |
| Content-only change (new names in docs, old repo names kept) | Minimal effort | Name/content divergence, worse discoverability, rename debt accumulates |

## Decision

Rename the six repos **in place** via the GitHub API, in dependency order
(governance → templates → bootstrap), after all content of all six repos has
been updated in the same release wave. GitHub keeps history, branches,
issues, stars and the `is_template` flag, and 301-redirects every old URL —
no consumer hard-breaks.

Content references inside the six repos are updated with a **three-pattern,
exclusion-protected** replacement (never a bare `itshaker → vibecoding`
global), executed in the same order governance → templates → bootstrap, with
an audit grep (expected: no residual family references) run before every
commit.

**Explicitly excluded from the content replacement (must remain as-is):**
- every reference to `itshaker-dgx-spark-V2` (project name, unchanged);
- every reference to `ITShaker-llmwiki`;
- `.hermes/plans/*` historical session snapshots (records of past sessions —
  renaming inside them would falsify the record; old names keep resolving
  via GitHub redirects anyway);
- accepted historical ADRs (ADR-0001, ADR-0002): immutable decision records
  written when the ecosystem was called `itshaker`; their descriptive
  mentions of the ecosystem name stay as authored (repo-name references were
  still updated to keep links resolvable — ADR redirects handle the rest).

Consequential renames outside the six repos, in the same wave:
- local workspace `/opt/data/workspace/itshaker-align/` → `vibecoding-align/`
  (the six working clones plus `itshaker-dgx-spark-V2` and `ITShaker-llmwiki`
  which stay in place);
- VPS2 skill `itshaker-governance-sync` references and directory;
- DGX Spark host allowlist
  `docker/hermes-spark-builder/capabilities/github-repository-allowlist.yml`
  (entries `lowcodai/itshaker-bootstrap`, `lowcodai/itshaker-copilot-governance`,
  `lowcodai/itshaker-template-ai` → `lowcodai/vibecoding-*`).

## Consequences

- Old clone/URLs keep working via 301 redirects — no consumer breaks hard;
  new consumers use `vibecoding-*` names.
- New projects instantiated after this date reference `vibecoding-template-*`
  (the four `source_repo:` values in `vibecoding-bootstrap/config/templates.yml`
  are updated in the same wave).
- `standards/naming-conventions.md` — the only living spec encoding the old
  pattern — is updated in the same commit wave; skill slugs (external,
  installed on-site) are **not** renamed.
- Documented env vars `ITSHAKER_GOVERNANCE_DIR` / `ITSHAKER_GITHUB_ORG`
  (`vibecoding-bootstrap/docs/usage.md`) are renamed to `VIBECODING_*`; they are
  not read by any script (verified 2026-09-15), so this is a documentation-only
  change.
- The DGX Spark allowlist must be updated in place on the Spark host
  filesystem (host-only repo, never cloned elsewhere) — otherwise the next
  hermes-spark-builder operation against `vibecoding-template-ai` silently 404s.
- Business projects keep their names: a future `itshaker-*` → `vibecoding-*`
  move for them would require its own ADR.
