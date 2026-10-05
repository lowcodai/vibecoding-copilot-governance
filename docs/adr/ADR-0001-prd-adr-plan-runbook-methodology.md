# ADR-0001 — Adopter la chaîne PRD → ADR → Plan → Runbook, avec deux modes d'exécution

**Date:** 2026-09-14
**Statut:** Accepted — language clause superseded by ADR-0002; Mode B (`hermes-orchestrator-openhands`) superseded by ADR-0005; Plan location amended by ADR-0006; execution mode names amended by ADR-0007
**Décideurs:** Capitaine (Jérémie Coste), Arcane (Hermes)
**Contexte technique:** gouvernance itshaker (templates, agents Copilot, méthodologie) — repo `vibecoding-copilot-governance`.
**authored_by:** frontier-model (cet ADR est rédigé par Claude Sonnet 5 dans ce plan)
**execution_mode:** hermes-solo (l'implémentation de ce plan lui-même se fait en Mode A — pas de délégation OpenHands nécessaire pour du travail documentaire/gouvernance)

> **Registry note (2026-09-29):** The former status line ("Proposé — Superseded by ADR-0002") read as if
> the whole decision were void, whereas ADR-0002 supersedes only its language clause and the
> PRD → ADR → Plan → Runbook chain it created is in force. "Accepted" is inferred from ADR-0002,
> ADR-0003 and ADR-0004, which all treat this ADR as accepted and implemented. The bilingual
> templates cited in §Références (`*.fr.md` / `*.en.md`) were merged into `templates/PRD-template.md`
> and `templates/ADR-template.md` by ADR-0002 (IMP-002). Body kept in French as authored (ADR-0002, NEG-001).

## Contexte

Absence de convention PRD/ADR dans la gouvernance itshaker jusqu'à ce jour : les repos
consommateurs (`itshaker-dgx-spark-V2`, `HermesVPS2`, etc.) ont chacun développé leurs propres
usages ad hoc pour documenter intention et décision technique, sans structure partagée ni agent
dédié. Un agent qui commence à coder sans intention documentée (PRD) ni décision technique
tracée (ADR) optimise localement sans garantie de cohérence globale — un problème aggravé pour
un agent en inférence locale (Qwen3.8-27B-NVFP4 sur DGX Spark) qui a besoin que l'arbitrage des
questions ambiguës ait déjà eu lieu en amont, pas en cours d'exécution.

Par ailleurs, deux modes de développement réels coexistent déjà dans l'écosystème itshaker :
un agent Hermes qui exécute seul (Mode A), et un pattern d'orchestration Hermes → OpenHands déjà
accepté par `ADR-0020` de `itshaker-dgx-spark-V2` pour `hermes-spark-builder` (Mode B). Aucun de
ces deux modes n'était formalisé au niveau de la gouvernance transverse.

## Options considérées

| Option | Avantages | Inconvénients |
|--------|-----------|---------------|
| Statu quo (pas de convention PRD/ADR partagée) | Aucun effort immédiat | Dérive continue de la documentation, incohérence entre repos, agents locaux sans garde-fou |
| Convention PRD/ADR/Plan/Runbook avec modèle frontière obligatoire | Qualité maximale garantie | Coût opérationnel élevé, rejeté par le Capitaine (2026-09-14) pour raison de coût |
| Convention PRD/ADR/Plan/Runbook, modèle frontière recommandé non bloquant, deux modes d'exécution (A/B) | Flexibilité de coût, généralise un pattern déjà validé (ADR-0020), traçabilité intention→décision→exécution | Charge documentaire supplémentaire avant tout travail ; risque de qualité inégale si systématiquement en local-model sans relecture |

## Décision

Nous choisissons **la convention PRD/ADR/Plan/Runbook avec recommandation de modèle frontière
non bloquante et deux modes d'exécution (Hermes Solo / Hermes Orchestrateur + OpenHands)**
parce qu'elle formalise un pattern déjà validé en pratique (`ADR-0020`), respecte la contrainte
de coût du Capitaine sans sacrifier l'audit (champ `authored_by`), et sépare clairement
intention (PRD), décision (ADR), exécution planifiée (Plan) et détail opérationnel (Runbook).

Détail complet de la chaîne, des critères de choix de mode et des templates : voir
`docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`.

## Conséquences

### Positives
- Traçabilité intention → décision → exécution pour tout futur travail gouverné par
  `vibecoding-copilot-governance`.
- Flexibilité de coût : un PRD/ADR `local-model` reste valide et exécutable, jamais bloqué.
- Généralisation d'un pattern déjà validé (`ADR-0020`) plutôt qu'invention d'un nouveau.

### Négatives
- Charge documentaire supplémentaire avant tout travail (PRD + ADR avant le premier commit de
  code pour tout travail non trivial).
- Risque de PRD/ADR de qualité inégale si systématiquement rédigés en local-model sans relecture
  frontière — mitigation documentée (recommandation forte + audit `authored_by`), pas
  d'enforcement automatique.

### Neutres / À surveiller
- Le grain de `execution_mode` est choisi par ADR (pas par repo) — un même repo peut mélanger
  Mode A et Mode B selon la décision. À reconsidérer si le Capitaine préfère un défaut par repo.
- Mode B dépend de prérequis externes non garantis (voir skill `openhands-spark-ops` —
  limitations connues au 2026-09-14).

## Mise en œuvre

Voir le plan `.hermes/plans/2026-09-14_122246-prd-adr-methodology-and-execution-modes.md`
(Tâches 1 à 14) : templates PRD/ADR bilingues, agents `prd-generator`/`adr-generator`, document
de méthodologie, synchronisation via `sync-governance.sh`, et rétro-application de la langue
déclarée sur les repos existants.

## Références

- `itshaker-dgx-spark-V2/docs/adr/ADR-0020-hermes-builder-openhands-orchestration.md`
- `docs/methodology/PRD-ADR-PLAN-RUNBOOK-WORKFLOW.md`
- `templates/PRD-template.{fr,en}.md`, `templates/ADR-template.{fr,en}.md`
- `agents/prd-generator.agent.md`, `agents/adr-generator.agent.md`
