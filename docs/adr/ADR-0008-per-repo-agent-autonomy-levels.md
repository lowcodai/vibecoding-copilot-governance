# ADR-0008 — Per-repository agent autonomy levels

**Date:** 2026-10-23
**Status:** Accepted (2026-10-23, Capitaine)
**Decision makers:** Capitaine (Jérémie Coste)
**Technical context:** dev factory kit (`dev-factory/project-template/`) copied into every consumer
repo by `vibecoding-bootstrap`; Claude Code sessions (interactive and orchestrated by
`scripts/orchestrate.py`); GitHub repositories without branch protection on `main` (private repos
on a GitHub Free account cannot have it).
**authored_by:** frontier-model
**execution_mode:** single-agent (governance and kit change, implemented and tested in this repo
and in `vibecoding-bootstrap`)
**amends:** ADR-0005 (DEC-006 git model; DEC-002/DEC-004 at level `trusted` only; IMP-006 sync
behaviour for kit files)

## Context

- **CTX-001**: Guard rails are hard-coded in the kit and identical for every repo: deny rules in
  `.claude/settings.json` (git push/merge/rebase, curl, wget, gh, ...), patterns in
  `.claude/hooks/tool_guardian.py`, the role table and "Never" list in `AGENTS.md`, one line in
  `CLAUDE.md`, the DEV role prompt and the task template.
- **CTX-002**: During a production incident on `arcane3m6` (2026-10-22) the agent could neither
  probe HTTP endpoints (`Bash(curl:*)` denied) nor push its fix (`git push` denied by the deny
  rule **and** by `tool_guardian`). The Capitaine decided to lift both in that repo, autonomous
  agents included. Doing this by hand per repo means editing two human-owned files under
  `.claude/` plus at least five texts that still say "never push".
- **CTX-003**: The layers are inconsistent today: curl/wget/gh are blocked only by deny rules;
  `git pull` is blocked by nothing; commits on `main` are forbidden only in text; secrets reads are
  denied only for `Read(./.env*)` at the root; `.ai/roles/` and `scripts/orchestrate.py` are
  protected only by the orchestrator, after the fact.
- **CTX-004**: `sync-governance.sh` copies kit files only when absent, so a re-sync can neither
  change guard rails nor deliver kit fixes to an existing repo.
- **CTX-005**: No repo has branch protection on `main`. Once agents may push, client-side checks
  are the only barrier in front of `main` unless the repo enables branch protection.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Keep one hard-coded policy, edit repos by hand | No new tooling | Drift; every exception is two `.claude/` edits plus texts; nothing records the choice |
| Level chosen by an environment variable | Trivial to switch | An agent (or a stray shell) can raise its own level; not versioned, not reviewable |
| **Level in a protected, versioned file; every guard-rail artefact derived from it** | One reviewable choice per repo; agents cannot raise it; layers cannot disagree; re-sync applies it | A policy module and a renderer to maintain; sync must overwrite kit-owned files |

## Decision

- **DEC-001 — Three levels.** Each repo declares one level. The default, and the fallback for a
  missing, unreadable or invalid declaration, is `supervised`.

  | Action | `supervised` | `branch` | `trusted` |
  |---|---|---|---|
  | Commit on a non-base branch | yes | yes | yes |
  | Push the current non-base branch (interactive session) | no | yes | yes |
  | Push the task branch and open a draft PR (orchestrated run) | no | orchestrator, at `READY_FOR_APPROVAL` | same |
  | Merge the base branch into the current branch (interactive) | no | yes | yes |
  | Merge into the base branch, rebase, `git pull` | no | no | no |
  | curl/wget (subject to DEC-002) | no | yes | yes |
  | `gh` read-only (`pr view/list/checks/diff`, `run view/list`, `issue view`, `api` GET) | no | yes | yes |
  | `gh pr create --draft`, `gh pr comment` (interactive) | no | yes | yes |
  | `gh pr merge` of the session's own PR when all checks are green (interactive) | no | no | yes |
  | Merge after human approval (orchestrated) | human | human | orchestrator, after `orchestrate.py approve` |

  In orchestrated runs the DEV agent never pushes at any level: `scripts/orchestrate.py` pushes
  deterministically once REVIEW and TEST have passed, so unreviewed intermediate states are never
  published. REVIEW and TEST keep read-only tools at every level. Human approval of an orchestrated
  task stays mandatory at every level.
- **DEC-002 — Invariants, at every level.** No force push in any form (`--force`,
  `--force-with-lease`, `+refspec`, `--mirror`, `--delete`); no push to, commit on or merge into
  the base branch; no tag push; no `--no-verify`, no `rebase`, no `gh pr merge --admin`; no git
  configuration that redirects pushes or hooks (`remote.*.push`, `push.*`, `url.*.insteadOf`,
  `core.hooksPath`); no reading or committing secrets (`.env*`, keys, credentials) by any tool; no
  `sudo`, recursive deletion of roots, block-device writes or `chmod 777`; no exfiltration (`curl`
  or `wget` piped to a shell, upload of local files, `gh api` with a method other than GET); no
  publication or infrastructure change (`npm publish`, `docker push`, `terraform apply`,
  `kubectl delete`, ...) outside a Runbook; no change to protected paths (DEC-004); the secrets
  scanner and the `secrets-scan` validation cannot be disabled by an agent.
- **DEC-003 — Single source of truth.** The level lives in `.ai/autonomy.yaml` in the target repo
  (`level: supervised | branch | trusted`). It never comes from an environment variable. The
  effective level is the **most restrictive** of the working-tree file and the file committed on
  the base branch, so a change takes effect only once a human has merged it.
- **DEC-004 — Protected.** `.ai/autonomy.yaml` joins the protected paths (`.claude/`,
  `.ai/orchestration.yaml`, `.ai/roles/`, `scripts/orchestrate.py`), enforced in all three
  layers: deny rules, `tool_guardian`, and the orchestrator's protected-paths check.
- **DEC-005 — Derived, not duplicated.** One policy module in the kit defines what each level
  allows. `.claude/settings.json` and the managed autonomy blocks of `CLAUDE.md` and `AGENTS.md`
  are rendered from it; `tool_guardian.py` and `orchestrate.py` read the effective level at run
  time through the same module. A consistency check fails when a rendered file does not match the
  declared level.
- **DEC-006 — Who changes the level.** A human, by running
  `sync-governance.sh --autonomy <level>` (or `new-project.sh --autonomy <level>` at creation),
  then reviewing and merging the resulting diff.
- **DEC-007 — Kit-owned files are refreshed by sync.** Files the kit owns (`.claude/settings.json`,
  `.claude/hooks/*.py`, the policy module, `scripts/orchestrate.py`) are overwritten on every
  sync; project-tuned files (`.ai/orchestration.yaml`, `.ai/roles/`, `CLAUDE.md` outside its
  managed block, the secrets allowlist, the docs skeleton) are still never overwritten. This
  amends ADR-0005 IMP-006.
- **DEC-008 — DEV keeps its hooks.** The orchestrated DEV run must not use `--bare` (fixed
  2026-10-23: the common runner command carried it, so DEV ran without hooks).
- **DEC-009 — Branch protection recommended, not required.** Repos at `branch` or `trusted`
  should enable branch protection on `main` (PR required, force push and deletion blocked) where
  their plan allows it; where it does not, the client-side checks of DEC-002 are the only barrier
  and the repo's README says so.

## Consequences

### Positive
- **POS-001**: Lifting push and curl for a repo is one reviewed command, not hand edits.
- **POS-002**: Deny rules, hook, orchestrator and texts can no longer disagree for a given level.
- **POS-003**: An agent cannot raise its own level: the file is protected and only the committed
  base-branch version can widen the effective level.
- **POS-004**: Kit fixes (such as DEC-008) reach existing repos on the next sync.

### Negative
- **NEG-001**: Without branch protection, `branch` and `trusted` rely on client-side parsing of
  git and gh commands; the parser accepts a narrow allow-list and refuses everything else.
- **NEG-002**: Overwriting kit-owned files removes local hand edits to `.claude/settings.json`;
  project-specific rules must move into the level file (more restrictive only) or into the kit.
- **NEG-003**: More code in the kit (policy module, renderer, push/PR step in the orchestrator).

### Neutral / To monitor
- **NEU-001**: Hermes and GitHub Copilot keep their own guard rails; this ADR governs Claude Code
  sessions in the repo (interactive and orchestrated).
- **NEU-002**: `trusted` is defined but no repo is expected to use it before `branch` has run for
  a while.

## Implementation

- **IMP-001**: Governance kit: `.ai/autonomy.yaml` (default `supervised`), the policy module and
  renderer under `.claude/hooks/`, `tool_guardian.py` reading the effective level, generated
  `.claude/settings.json`, orchestrator push/PR at `READY_FOR_APPROVAL` and merge on `approve` at
  `trusted`, `autonomy.yaml` in `git.protected_paths`, managed blocks in `CLAUDE.md`, an
  `autonomy-check` validation; `dev-factory/README.md` (guard-rails table),
  `standards/branching.md`, `policies/branch-protection.md`, the Hermes skill and the methodology.
- **IMP-002**: Bootstrap: `new-project.sh --autonomy <level>` (default `supervised`, shown in
  `--dry-run`, documented in `--help`); `sync-governance.sh --autonomy <level>` writes the level
  file and re-renders the managed files; the generated `AGENTS.md` carries a managed autonomy
  block; the five templates ship at `supervised`.
- **IMP-003**: Tests: per level, allowed and refused commands through the hook, rendered deny
  rules, orchestrator behaviour (push/PR, merge on approve); invariants at every level; fallback
  to `supervised` for a missing or corrupt file; base-branch value wins when more restrictive;
  re-sync keeps tuned files and changes only what the level drives.
- **Error behaviour**: any failure to read or parse the level resolves to `supervised`; a failed
  orchestrator push or merge leaves the task in its state (`READY_FOR_APPROVAL` / `APPROVED`) with
  the reason logged, for a human to finish.
- **Rollback condition**: an agent action at `branch` or `trusted` that reaches the base branch
  without human review sets every repo back to `supervised` and reopens this ADR.

## References

- **REF-001**: ADR-0005 — sequential Claude Code team (amended here).
- **REF-002**: ADR-0007 — agent-neutral project contract.
- **REF-003**: `policies/branch-protection.md`, `standards/branching.md`.
- **REF-004**: Incident 2026-10-22 on `arcane3m6` (curl and push denied during production repair).
