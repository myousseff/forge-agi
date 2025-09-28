# Observability (v0.2)
Recommandation de champs:
- runs: id, created_at, git_sha, flutter_version, apk_size_bytes, coverage, lint_errors, apk_sha256
- artifacts: id, run_id, path, type (apk|coverage|critic|verifier|judge|spec|logs), kpis JSON

Conserver les artefacts dans un répertoire `runs/<timestamp>/` + upload CI.
