# Branch Protection Policy — vibecoding

## Rules for `main`

Configure via GitHub Branch Protection Rules or Ruleset:

```yaml
# Via GitHub Rulesets (recommended)
- require_pull_request: true
  required_approving_review_count: 1
  dismiss_stale_reviews: true
- require_status_checks: true
  required_checks:
    - ci
    - governance-check
- require_linear_history: false  # squash and merge is enough
- block_force_pushes: true
- block_deletions: true
- require_signed_commits: false  # optional, recommended for sensitive projects
```

## Configuration via GitHub CLI

```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

## Autonomy levels `branch`, `trusted` and `yolo` (ADR-0008, ADR-0009)

Agents may push their own branch (and, at `trusted` and `yolo`, merge their own green PR; at `yolo`
without any human approval). Branch protection on
`main` is the server-side backstop for the invariants (no push to `main`, no force push, no merge
without checks): enable it on every repo above `supervised` where the plan allows it. Private
repositories on a GitHub Free plan cannot use branch protection or rulesets; for them the
client-side checks of `tool_guardian.py` are the only barrier — say so in the repo's README.

## Session Auto-Commit

The `session-auto-commit` hook is **forbidden on `main`**.
It must never be configured without a dedicated feature branch.

## Deployment environments

Configure GitHub environments with protection for `production`:
- Required reviewers
- Recommended wait timer (15 minutes minimum)
