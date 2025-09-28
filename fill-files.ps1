# Script PowerShell pour remplir les fichiers avec le contenu approprié
# Auteur: Assistant IA

Write-Host "Remplissage des fichiers avec le contenu..." -ForegroundColor Green

# Fonction pour écrire du contenu dans un fichier
function Write-FileContent {
    param([string]$Path, [string]$Content)
    Set-Content -Path $Path -Value $Content -Encoding UTF8
    Write-Host "Rempli: $Path" -ForegroundColor Cyan
}

# Dockerfile Flutter
$dockerfileFlutter = @'
# Dockerfile pour Flutter
FROM ubuntu:20.04

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Installation de Flutter
ENV FLUTTER_HOME=/opt/flutter
ENV PATH=$PATH:$FLUTTER_HOME/bin
RUN git clone https://github.com/flutter/flutter.git $FLUTTER_HOME
RUN flutter doctor

# Définition du répertoire de travail
WORKDIR /app

# Commande par défaut
CMD ["flutter", "doctor"]
'@

# Dockerfile API
$dockerfileApi = @'
# Dockerfile pour FastAPI
FROM python:3.11-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'@

# Dockerfile Worker
$dockerfileWorker = @'
# Dockerfile pour Celery Worker
FROM python:3.11-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Commande de démarrage du worker
CMD ["celery", "-A", "worker", "worker", "--loglevel=info"]
'@

# Docker Compose
$dockerCompose = @'
version: '3.8'

services:
  api:
    build:
      context: ../services/api
      dockerfile: ../../infra/docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/forge_agi
    depends_on:
      - db
      - redis

  worker:
    build:
      context: ../services/worker
      dockerfile: ../../infra/docker/Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/forge_agi
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=forge_agi
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
'@

# GitHub Workflow
$githubWorkflow = @'
name: Build APK

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build-apk:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.19.0'
        channel: 'stable'
    
    - name: Install dependencies
      run: flutter pub get
    
    - name: Build APK
      run: flutter build apk --release
    
    - name: Upload APK
      uses: actions/upload-artifact@v4
      with:
        name: app-release
        path: build/app/outputs/flutter-apk/app-release.apk
'@

# README
$readme = @'
# Forge AGI

Plateforme de génération automatique d'applications mobiles basée sur des spécifications.

## Architecture

```
forge-agi/
  apps/
    ui/                  # Dashboard Next.js minimal (à venir)
  bricks/
    mobile_app_base/     # Mason brick Flutter pilotée par la Spec
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
- Validation des spécifications
- Orchestration des processus
- Endpoints REST

### Worker (Celery)
- Génération de code
- Build des applications
- Tests automatisés
- Packaging

### UI (Next.js) - À venir
- Dashboard minimal
- Interface de gestion des projets

## Démarrage rapide

1. Cloner le repository
2. Naviguer vers le dossier infra
3. Lancer avec Docker Compose:

```bash
cd infra
docker-compose up -d
```

## Développement

### Prérequis
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

## Spécifications

Les applications sont générées à partir de fichiers YAML définissant:
- Structure de l'interface
- Modèles de données
- Logique métier
- Configuration de build

Voir `specs/examples/resa.yaml` pour un exemple complet.

## Licence

MIT
'@

# Schema JSON
$schema = @'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Mobile App Specification",
  "version": "0.1.0",
  "type": "object",
  "properties": {
    "app": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "Nom de l'application"
        },
        "package": {
          "type": "string",
          "description": "Package name (ex: com.example.app)"
        },
        "version": {
          "type": "string",
          "description": "Version de l'application"
        }
      },
      "required": ["name", "package", "version"]
    },
    "screens": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "type": {
            "type": "string",
            "enum": ["list", "detail", "form", "login", "dashboard"]
          },
          "widgets": {
            "type": "array",
            "items": {
              "type": "object"
            }
          }
        },
        "required": ["name", "type"]
      }
    },
    "models": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "fields": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {
                  "type": "string"
                },
                "type": {
                  "type": "string",
                  "enum": ["string", "int", "double", "bool", "datetime"]
                },
                "required": {
                  "type": "boolean"
                }
              },
              "required": ["name", "type"]
            }
          }
        },
        "required": ["name", "fields"]
      }
    }
  },
  "required": ["app", "screens", "models"]
}
'@

# Exemple de spécification
$exampleSpec = @'
app:
  name: "Resa App"
  package: "com.example.resa"
  version: "1.0.0"

screens:
  - name: "login"
    type: "login"
    widgets:
      - type: "TextField"
        label: "Email"
        field: "email"
      - type: "TextField"
        label: "Mot de passe"
        field: "password"
        obscureText: true
      - type: "Button"
        text: "Se connecter"
        action: "login"

  - name: "reservations"
    type: "list"
    title: "Mes réservations"
    widgets:
      - type: "ListView"
        itemBuilder: "reservation_item"
        dataSource: "reservations"

  - name: "reservation_detail"
    type: "detail"
    title: "Détails réservation"
    widgets:
      - type: "Text"
        field: "title"
        style: "title"
      - type: "Text"
        field: "date"
        style: "subtitle"
      - type: "Text"
        field: "description"

models:
  - name: "User"
    fields:
      - name: "id"
        type: "int"
        required: true
      - name: "email"
        type: "string"
        required: true
      - name: "name"
        type: "string"
        required: true

  - name: "Reservation"
    fields:
      - name: "id"
        type: "int"
        required: true
      - name: "title"
        type: "string"
        required: true
      - name: "description"
        type: "string"
        required: false
      - name: "date"
        type: "datetime"
        required: true
      - name: "userId"
        type: "int"
        required: true
'@

# Requirements API
$apiRequirements = @'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
celery==5.3.4
redis==5.0.1
pyyaml==6.0.1
jinja2==3.1.2
'@

# Requirements Worker
$workerRequirements = @'
celery==5.3.4
redis==5.0.1
pyyaml==6.0.1
jinja2==3.1.2
requests==2.31.0
'@

# Main API
$apiMain = @'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import yaml
import json
import os

app = FastAPI(title="Forge AGI API", version="1.0.0")

class SpecValidationRequest(BaseModel):
    spec_content: str

class SpecValidationResponse(BaseModel):
    valid: bool
    errors: list = []

@app.get("/")
async def root():
    return {"message": "Forge AGI API - Service de génération d'applications mobiles"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "forge-agi-api"}

@app.post("/validate-spec")
async def validate_spec(request: SpecValidationRequest):
    """Valide une spécification YAML"""
    try:
        # Charger le schéma JSON
        schema_path = "../../specs/schema/mobile-app-0.1.0.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Parser le YAML
        spec_data = yaml.safe_load(request.spec_content)
        
        # Validation basique (à améliorer avec jsonschema)
        required_fields = ["app", "screens", "models"]
        errors = []
        
        for field in required_fields:
            if field not in spec_data:
                errors.append(f"Champ requis manquant: {field}")
        
        return SpecValidationResponse(
            valid=len(errors) == 0,
            errors=errors
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-app")
async def generate_app(request: SpecValidationRequest):
    """Déclenche la génération d'une application"""
    try:
        # Validation de la spec
        validation = await validate_spec(request)
        if not validation.valid:
            raise HTTPException(status_code=400, detail="Spécification invalide")
        
        # TODO: Envoyer la tâche au worker Celery
        # task = generate_app_task.delay(request.spec_content)
        
        return {
            "message": "Génération d'application lancée",
            "task_id": "task_123"  # À remplacer par l'ID réel
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'@

# Main Worker
$workerMain = @'
from celery import Celery
import yaml
import json
import os
import subprocess
import tempfile
import shutil

# Configuration Celery
app = Celery('forge_agi_worker')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@app.task
def generate_app_task(spec_content: str, project_name: str = None):
    """Génère une application Flutter à partir d'une spécification YAML"""
    try:
        # Parser la spécification
        spec_data = yaml.safe_load(spec_content)
        
        if not project_name:
            project_name = spec_data.get('app', {}).get('name', 'generated_app').lower()
        
        # Créer un répertoire temporaire pour le projet
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = os.path.join(temp_dir, project_name)
            
            # Créer le projet Flutter
            subprocess.run([
                'flutter', 'create', '--org', 'com.example', project_name
            ], cwd=temp_dir, check=True)
            
            # Générer le code basé sur la spécification
            generate_code_from_spec(spec_data, project_path)
            
            # Build de l'APK
            subprocess.run([
                'flutter', 'build', 'apk', '--release'
            ], cwd=project_path, check=True)
            
            # TODO: Copier l'APK vers un stockage permanent
            apk_path = os.path.join(project_path, 'build/app/outputs/flutter-apk/app-release.apk')
            
            return {
                "success": True,
                "project_name": project_name,
                "apk_path": apk_path,
                "message": "Application générée avec succès"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de la génération"
        }

def generate_code_from_spec(spec_data: dict, project_path: str):
    """Génère le code Flutter basé sur la spécification"""
    # TODO: Implémenter la génération de code
    # - Générer les modèles de données
    # - Générer les écrans
    # - Générer la navigation
    # - Configurer les dépendances
    
    print(f"Génération du code pour le projet: {project_path}")
    print(f"Spécification: {spec_data}")

if __name__ == '__main__':
    app.start()
'@

# Écrire le contenu dans les fichiers
Write-FileContent "infra/docker/Dockerfile.flutter" $dockerfileFlutter
Write-FileContent "infra/docker/Dockerfile.api" $dockerfileApi
Write-FileContent "infra/docker/Dockerfile.worker" $dockerfileWorker
Write-FileContent "infra/docker-compose.yml" $dockerCompose
Write-FileContent ".github/workflows/build-apk.yml" $githubWorkflow
Write-FileContent "README.md" $readme
Write-FileContent "specs/schema/mobile-app-0.1.0.json" $schema
Write-FileContent "specs/examples/resa.yaml" $exampleSpec
Write-FileContent "services/api/requirements.txt" $apiRequirements
Write-FileContent "services/worker/requirements.txt" $workerRequirements
Write-FileContent "services/api/main.py" $apiMain
Write-FileContent "services/worker/main.py" $workerMain

Write-Host "`nTous les fichiers ont ete remplis avec succes!" -ForegroundColor Green
Write-Host "`nProchaines etapes:" -ForegroundColor Yellow
Write-Host "1. Naviguer vers le dossier infra: cd infra" -ForegroundColor White
Write-Host "2. Lancer les services: docker-compose up -d" -ForegroundColor White
Write-Host "3. Acceder a l'API: http://localhost:8000" -ForegroundColor White
Write-Host "4. Voir la documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`nDocumentation disponible dans README.md" -ForegroundColor Cyan
