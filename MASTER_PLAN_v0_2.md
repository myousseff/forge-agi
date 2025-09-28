# Forge AGI — Master Plan (v0.2) — 2025-09-28

## Objectif
Arrêter la divagation des agents (Cursor) et livrer des **artefacts concrets, déterministes et auditables** (APK, README, rapports Critic/Verifier/Judge) à partir d’une **Spec** déclarative unique.

## Invariants (non-négociables)
- Aucun code d’app n’est généré par LLM. Seuls **bricks Mason** produisent le code.
- Toute exécution est **reproductible** (versions épinglées, seeds, hashs, artefacts horodatés).
- Spécification **schema v0.2.0** strictement validée avant toute génération.
- Observabilité minimale: temps, coûts (si pertinents), hashs, taille APK, lints, coverage.

## DSL mobile_app — schema v0.2.0 (résumé)
- **Nouveaux blocs**: `workflows`, `i18n`, `seed`, `assets`, `feature_flags`, `indexes.composite`, `ci.signing`, `telemetry`.
- **Raffinements**: `security.rules` structurées, `ui.widgets` cohérents, validations de champs, `auth_providers`.
- **Plateformes**: Android uniquement pour MVP (iOS ultérieur).

## Exemple de Spec (YAML)
(inclus dans `examples/spec_example_v0_2.yaml` de ce package)

## Runbook: 90 minutes → APK
1. Valider `spec.yaml` contre `schema/mobile_app/0.2.0/schema.json`.
2. Générer via **Mason bricks** (déterministe).
3. Injecter `seed` + `assets` (hachage).
4. Lancer `flutter analyze`, tests unitaires + tests d’intégration `workflows`.
5. `flutter build apk --release` (unsigned).
6. Collecter artefacts: `apk`, `coverage`, `critic_report.json`, `verifier_report.json`, `judge_verdict.json`, `spec.json`, `git_sha.txt`.
7. DoD: APK buildable < 12 min, 0 erreurs lint, ≥ 80% coverage (couche critique), hash fixe, README généré.

## Rôles d’agents (prompts contractuels)
- **planner@1.1.0**: produit `spec.yaml` v0.2 ou `spec_diff.yaml`. Jamais de code app.
- **critic@1.1.0**: `critic_report.json` (blocking/non_blocking/suggestions).
- **verifier@1.1.0**: `verifier_report.json` (tests, lints, durée, tailles, sha256).
- **judge@1.1.0**: `judge_verdict.json` (decision/reasons/proposed_actions).

Prompts prêts à l’emploi: voir `prompts/`.

## Audit & Drift
Commande à donner à Cursor: voir `prompts/audit_prompt.md`. Génère `AUDIT.md` + sorties brutes `audit/raw/*.txt`.

## Observabilité (DB/FS)
Tables/champs recommandés: voir `observability/README.md`.

## DoD (Definition of Done) v0.2
- `spec.yaml` v0.2 valide + hash
- APK release unsigned + sha256 + taille
- `README.md` généré (install, build, test)
- `critic_report.json`, `verifier_report.json`, `judge_verdict.json` archivés
- KPIs persistés et consultables (runs/artifacts)

## Roadmap courte
- D1: Normaliser la Spec, auditer repo, branch `mvp/mobile_v0.2`, CI pin.
- D2: Premier run E2E, livraison APK + rapports, gel des invariants.
- D3: Ajout i18n, workflows additionnels, seeds enrichis, flags de features.

— Fin —
