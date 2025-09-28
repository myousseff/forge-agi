# Forge AGI

Plateforme de gÃ©nÃ©ration automatique d'applications mobiles basÃ©e sur des spÃ©cifications.

## Architecture

```
forge-agi/
  apps/
    ui/                  # Dashboard Next.js minimal (Ã  venir)
  bricks/
    mobile_app_base/     # Mason brick Flutter pilotÃ©e par la Spec
  services/
    api/                 # FastAPI (validation, orchestrateur, endpoints)
    worker/              # Celery worker (codegen + build + tests + packager)
  infra/
    docker/
      Dockerfile.flutter # Runner Flutter pin
      Dockerfile.api
      Dockerfile.worker
    docker-compose.yml
  specs/
    examples/resa.yaml   # Spec d'exemple
    schema/mobile-app-0.1.0.json
  .github/workflows/build-apk.yml
```

## Services

### API (FastAPI)
- Validation des spÃ©cifications
- Orchestration des processus
- Endpoints REST

### Worker (Celery)
- GÃ©nÃ©ration de code
- Build des applications
- Tests automatisÃ©s
- Packaging

### UI (Next.js) - Ã€ venir
- Dashboard minimal
- Interface de gestion des projets

## DÃ©marrage rapide

### Avec Docker (recommandé)

1. Cloner le repository
2. Builder et lancer la stack complète :

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

3. Tester l'API :

```bash
curl http://127.0.0.1:8080/v1/health
# Doit renvoyer : {"ok": true}
```

4. Accéder au runner Flutter :

```bash
docker compose -f infra/docker-compose.yml run --rm runner_flutter bash
```

## DÃ©veloppement

### PrÃ©requis
- Python 3.11+
- Flutter 3.19.0+
- Docker & Docker Compose
- Node.js 18+ (pour le dashboard)

### Installation locale

```bash
# Services API
cd services/api
pip install -r requirements.txt
uvicorn main:app --reload

# Worker
cd services/worker
pip install -r requirements.txt
celery -A worker worker --loglevel=info
```

### Worker dry-run

Le worker peut être exécuté en mode dry-run pour tester le pipeline sans génération de code Flutter :

#### Dans le conteneur Docker
```bash
# Builder le worker
docker compose -f infra/docker-compose.yml build worker

# Lancer le pipeline avec la spec d'exemple
docker compose -f infra/docker-compose.yml run --rm worker bash -lc "python -m worker.pipeline --spec /workspace/specs/examples/resa.yaml"
```

#### En local (avec le script de développement)
```bash
# Lancer le pipeline en local
python scripts/dev_run_pipeline.py specs/examples/resa.yaml
```

#### Résultats
Le pipeline crée la structure suivante dans `./work/<run_id>/artifacts/` :
- `spec.yml` - Spécification copiée
- `critic_report.json` - Rapport des contrôles logiques
- `verifier_report.json` - Rapport des vérifications statiques (placeholder)
- `judge_report.json` - Rapport de décision finale
- `source.zip` - Archive du dossier app/ (vide pour l'instant)
- `checksums.txt` - Checksums SHA256 de tous les fichiers

## SpÃ©cifications

Les applications sont gÃ©nÃ©rÃ©es Ã  partir de fichiers YAML dÃ©finissant:
- Structure de l'interface
- ModÃ¨les de donnÃ©es
- Logique mÃ©tier
- Configuration de build

Voir `specs/examples/resa.yaml` pour un exemple complet.

## Licence

MIT
