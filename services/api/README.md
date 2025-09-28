# Forge AGI API

API FastAPI minimale pour la validation de spécifications d'applications mobiles.

## Endpoints

### GET /v1/health
Endpoint de santé de l'API.
- **Réponse**: `{"ok": true}`

### POST /v1/specs/validate
Valide une spécification d'application mobile contre le schéma JSON.

**Request Body:**
```json
{
  "schema_version": "0.1.0",
  "spec": {
    "app": {
      "name": "Nom de l'app",
      "package": "com.example.app",
      "version": "1.0.0"
    },
    "screens": [...],
    "models": [...]
  }
}
```

**Réponse valide:**
```json
{
  "valid": true
}
```

**Réponse invalide:**
```json
{
  "valid": false,
  "errors": ["app: 'package' is a required property"]
}
```

## Installation et test

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancer l'API
```bash
uvicorn app.main:app --reload --port 8080
```

### 3. Exécuter les tests
```bash
pytest -q
```

### 4. Tests détaillés
```bash
pytest tests/test_api.py -v
```

## Structure des fichiers

```
services/api/
├── app/
│   ├── __init__.py
│   ├── main.py          # Application FastAPI
│   └── schemas.py       # Modèles Pydantic
├── tests/
│   ├── __init__.py
│   └── test_api.py      # Tests unitaires
├── requirements.txt     # Dépendances Python
└── README.md           # Documentation
```

## Validation du schéma

L'API utilise le schéma JSON situé dans `specs/schema/mobile-app-0.1.0.json` pour valider les spécifications d'applications mobiles.

Le schéma valide :
- **app**: Informations de base de l'application (name, package, version)
- **screens**: Liste des écrans avec leurs widgets
- **models**: Modèles de données avec leurs champs
