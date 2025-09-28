# Pipeline Forge AGI - Documentation

## Vue d'ensemble

Le pipeline Forge AGI est un système de génération automatique d'applications mobiles basé sur des spécifications YAML. Il fonctionne en mode "dry-run" sans génération de code Flutter, préparant la structure pour les étapes futures.

## Architecture du Pipeline

### Étapes du Pipeline

1. **VALIDATE_SPEC** - Validation de la spécification avec le schéma JSON
2. **CRITIC** - Contrôles logiques (références d'entités, sections obligatoires)
3. **CODEGEN_stub** - Création de la structure de répertoires
4. **STATIC_CHECKS_stub** - Placeholder pour les vérifications statiques
5. **TESTS_stub** - Placeholder pour les tests
6. **PACKAGE** - Empaquetage et calcul des checksums
7. **JUDGE** - Décision finale (accept/revise)

### Structure des Fichiers

```
services/worker/
├── __init__.py
├── main.py                 # Application Celery
├── requirements.txt        # Dépendances Python
├── worker/
│   ├── __init__.py
│   ├── main.py            # Configuration Celery
│   ├── pipeline.py        # Pipeline principal
│   ├── critic.py          # Contrôles logiques
│   └── judge.py           # Prise de décision
└── tests/
    └── test_pipeline.py   # Tests unitaires
```

## Utilisation

### Mode Docker (Recommandé)

```bash
# Builder le worker
docker compose -f infra/docker-compose.yml build worker

# Lancer le pipeline avec la spec d'exemple
docker compose -f infra/docker-compose.yml run --rm worker bash -lc "python -m worker.pipeline --spec /workspace/specs/examples/resa.yaml"
```

### Mode Local

```bash
# Installer les dépendances
cd services/worker
pip install -r requirements.txt

# Lancer le pipeline
python scripts/dev_run_pipeline.py specs/examples/resa.yaml
```

### CLI Direct

```bash
# Depuis le répertoire services/worker
python -m worker.pipeline --spec /path/to/spec.yaml --run-id optional-uuid
```

## Sorties

### Structure des Artifacts

Le pipeline crée la structure suivante dans `./work/<run_id>/` :

```
work/<run_id>/
├── app/                    # Dossier pour le code Flutter (vide pour l'instant)
├── artifacts/              # Artifacts de build
│   ├── spec.yml           # Spécification copiée
│   ├── critic_report.json # Rapport des contrôles logiques
│   ├── verifier_report.json # Rapport des vérifications statiques
│   ├── judge_report.json  # Rapport de décision finale
│   ├── source.zip         # Archive du dossier app/
│   └── checksums.txt      # Checksums SHA256
├── reports/               # Rapports intermédiaires
└── README_PLACEHOLDER.txt # Documentation générée
```

### Format des Rapports

#### critic_report.json
```json
{
  "issues": ["Liste des problèmes détectés"],
  "blocking": ["Problèmes critiques bloquants"],
  "critical_count": 0,
  "warning_count": 0
}
```

#### verifier_report.json
```json
{
  "format_ok": true,
  "analyze_ok": true,
  "lint_ok": true,
  "message": "Vérifications statiques simulées (placeholder)"
}
```

#### judge_report.json
```json
{
  "decision": "accept",
  "critic_ok": true,
  "static_ok": true,
  "tests_ok": true,
  "reason": "Tous les critères sont satisfaits"
}
```

## Configuration

### Variables d'Environnement

- `WORK_DIR` - Répertoire de travail (défaut: `/work`)
- `SCHEMA_PATH` - Chemin vers le schéma JSON (défaut: `specs/schema/mobile-app-0.1.0.json`)
- `WORKSPACE_PATH` - Chemin vers le workspace (défaut: `/workspace`)
- `REDIS_URL` - URL Redis pour Celery (défaut: `redis://localhost:6379/0`)

### Dépendances

```txt
celery==5.3.6
redis==5.0.1
pyyaml==6.0.1
jsonschema==4.19.0
rich==13.7.1
click==8.1.7
jinja2==3.1.2
requests==2.31.0
```

## Tests

### Tests Unitaires

```bash
cd services/worker
python -m pytest tests/ -v
```

### Test de Structure

```bash
python test_pipeline_structure.py
```

## Contrôles CRITIC

Le module CRITIC vérifie :

1. **Sections obligatoires** : `meta`, `app`, `data`, `ui`, `ci`
2. **Références d'entités** : Vérification que les écrans référencent des entités existantes
3. **Cohérence des données** : Validation des relations entre entités

### Exemple d'Erreur CRITIC

```json
{
  "issues": [
    "Écran 'Home': référence d'entité 'NonExistentEntity' inexistante"
  ],
  "blocking": [
    "Référence d'entité 'NonExistentEntity' inexistante"
  ],
  "critical_count": 1,
  "warning_count": 0
}
```

## Décision JUDGE

Le module JUDGE prend une décision basée sur :

- `critic_ok` : Aucun problème critique dans CRITIC
- `static_ok` : Vérifications statiques réussies
- `tests_ok` : Tests réussis

**Décision** :
- `accept` : Tous les critères sont satisfaits
- `revise` : Au moins un critère n'est pas satisfait

## Prochaines Étapes

1. **Intégration Mason/Flutter** - Génération de code Flutter réel
2. **Tests automatisés** - Tests unitaires et d'intégration
3. **Vérifications statiques** - Analyse de code et linting
4. **Build automatisé** - Compilation d'APK
5. **Déploiement** - Distribution automatique

## Dépannage

### Erreurs Communes

1. **Schéma non trouvé** : Vérifier `SCHEMA_PATH`
2. **Permissions** : Vérifier les droits d'écriture sur `WORK_DIR`
3. **Dépendances** : Installer toutes les dépendances Python
4. **Docker** : Vérifier que Docker est installé et en cours d'exécution

### Logs

Le pipeline utilise Rich pour l'affichage coloré des logs. Les erreurs sont affichées en rouge, les succès en vert.

## Support

Pour toute question ou problème, consulter :
- Les logs du pipeline
- Les rapports JSON générés
- Les tests unitaires
- La documentation des modules individuels
