# Repo Audit & Drift Report (à coller dans Cursor)
1) Exécute et capture la sortie brute (un fichier par commande sous `audit/raw/`):
- git rev-parse --abbrev-ref HEAD && git log --oneline -n 10
- git status -s
- tree -a -I node_modules -I .git -I build -I .dart_tool -I .venv -I dist
- grep -R --line-number --exclude-dir={.git,node_modules,.dart_tool,build} -E "TODO|FIXME|@deprecated" . || true
- dart --version || true && flutter --version || true
- python --version || true && node --version || true
- jq --version || true && yq --version || true

2) Valide la Spec `spec.yaml` contre `schema/mobile_app/0.2.0/schema.json`.
3) Vérifie workflows GitHub: checkout, setup-java, flutter-action, analyze, tests, build, upload-artifacts.
4) Vérifie Mason bricks (versions, variables). Aucun code Flutter produit par LLM (DRIFT si oui).
5) Si projet Flutter présent: `flutter analyze` + tests (sinon dry-run).
6) Génère `AUDIT.md`: State, Gaps, Drift risks, Action plan (D1/D2/D3).
