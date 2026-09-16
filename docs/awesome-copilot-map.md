# Awesome Copilot Distribution Map by Project Type

Source: [github/awesome-copilot](https://github.com/github/awesome-copilot)
Reference SHA: `dae77f24132c1d686c30fd5b29aee0d63668d1d2`

## Hooks

| Hook | base | infra | ai | app | m365 | Notes |
|------|:----:|:-----:|:--:|:---:|:----:|-------|
| `tool-guardian` | ✓ | ✓ | ✓ | ✓ | ✓ | Universal |
| `secrets-scanner` | ✓ | ✓ | ✓ | ✓ | ✓ | Universal |
| `governance-audit` | ✓ | ✓ | ✓ | ✓ | ✓ | Universal |
| `dependency-license-checker` | — | ✓ | ✓ | ✓ | ✓ | Projects with dependencies |
| `fix-broken-links` | ✓ | — | ✓ | ✓ | ✓ | Documentation |
| `session-logger` | — | — | ✓ | — | ✓ | AI sessions |
| `attester-import-check` | — | ✓ | ✓ | — | ✓ | Supply chain |
| `session-auto-commit` | — | — | opt | — | opt | Feature branch ONLY |

## Agents

| Agent | base | infra | ai | app | m365 |
|-------|:----:|:-----:|:--:|:---:|:----:|
| `adr-generator` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `runbook-generator` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `ai-readiness-reporter` | — | — | ✓ | — | ✓ |
| `agent-governance-reviewer` | — | — | ✓ | — | ✓ |
| `ai-team-dev` | — | — | ✓ | opt | — |
| `accessibility` | — | — | — | ✓ | — |
| `accessibility-runtime-tester` | — | — | — | ✓ | — |
| `declarative-agents-architect` | — | — | — | — | ✓ |
| `mcp-m365-agent-expert` | — | — | — | — | ✓ |

## Skills

| Skill | base | infra | ai | app | m365 |
|-------|:----:|:-----:|:--:|:---:|:----:|
| `acquire-codebase-knowledge` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `breakdown-plan` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `breakdown-epic-arch` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `breakdown-epic-pm` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `breakdown-feature-prd` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `breakdown-feature-implementation` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `breakdown-test` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `audit-integrity` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `agent-supply-chain` | — | ✓ | ✓ | — | — |
| `acreadiness-assess` | — | — | ✓ | — | — |
| `acreadiness-generate-instructions` | — | — | ✓ | — | — |
| `agent-governance` | — | — | ✓ | — | — |
| `agentic-eval` | — | — | ✓ | — | — |
| `ai-prompt-engineering-safety-review` | — | — | ✓ | — | — |
| `agent-owasp-compliance` | — | — | ✓ | opt | ✓ |
| `arize-instrumentation` | — | — | opt | — | — |
| `arize-dataset` | — | — | opt | — | — |
| `arize-evaluator` | — | — | opt | — | — |
| `arize-prompt-optimization` | — | — | opt | — | — |
| `mcp-create-declarative-agent` | — | — | — | — | ✓ |
| `declarative-agents` | — | — | — | — | ✓ |
| `entra-agent-user` | — | — | — | — | ✓ |
| `mcp-security-audit` | — | — | — | — | ✓ |
| `mcp-implementation-security-review` | — | — | — | — | ✓ |
| `threat-model-analyst` | — | — | — | — | ✓ |
| `secret-scanning` | — | — | — | — | ✓ |
| `mcp-deploy-manage-agents` | — | — | — | — | ✓ |
| `mcp-release-qa` | — | — | — | — | opt | Not on the pinned SHA above — see note below |
| `verify-agent-action` | — | — | — | — | opt | Not on the pinned SHA above — see note below |

## Plugins

| Plugin | base | infra | ai | app | m365 |
|--------|:----:|:-----:|:--:|:---:|:----:|
| `arch` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `acreadiness-cockpit` | — | — | ✓ | — | — |
| `ai-team-orchestration` | — | — | ✓ | opt | — |
| `arize-ax` | — | — | opt | — | — |
| `mcp-m365-copilot` | — | — | — | — | ✓ |

## Instructions

| Instruction | base | infra | ai | app | m365 |
|-------------|:----:|:-----:|:--:|:---:|:----:|
| `devops-core-principles` | ✓ | ✓ | — | — | — |
| `github-actions-ci-cd-best-practices` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `ansible` | — | ✓ | — | — | — |
| `containerization-docker-best-practices` | — | ✓ | opt | opt | — |
| `agent-safety` | — | — | ✓ | — | ✓ |
| `agent-skills` | — | — | ✓ | — | ✓ |
| `ai-prompt-engineering-safety-best-practices` | — | — | ✓ | — | ✓ |
| `a11y` | — | — | — | ✓ | — |
| `declarative-agents-microsoft365` | — | — | — | — | ✓ |
| `mcp-m365-copilot` | — | — | — | — | ✓ |
| `security-and-owasp` | — | — | — | — | ✓ |

> Legend: `✓` included by default, `opt` optional, `—` not applicable
>
> `m365` was added for `vibecoding-template-m365-agent` (Microsoft 365 Copilot declarative
> agents backed by an MCP server). Two of its skills (`mcp-release-qa`, `verify-agent-action`)
> did not exist at this map's pinned reference SHA and were sourced from a later commit
> (`9ce814859eaa473178a1463ee3aa0c54a8860b86`) when first added to
> `lowcodai/copilot-github-manager` — not wired into `install-awesome-copilot.sh`'s automated
> `m365` bundle for that reason; add manually per that repo's `.github/awesome-copilot-manifest.md`
> until the pinned SHA above is bumped to include them.
