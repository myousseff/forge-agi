# Scripts PowerShell pour Forge AGI

Ce document explique l'utilisation des scripts PowerShell créés pour initialiser et gérer le projet forge-agi.

## Scripts disponibles

### 1. `init-project.ps1` - Script principal (RECOMMANDÉ)
**Utilisation :** `powershell -ExecutionPolicy Bypass -File init-project.ps1`

Ce script orchestre tout le processus d'initialisation :
- ✅ Crée l'arborescence complète
- ✅ Remplit tous les fichiers avec le contenu approprié
- ✅ Vérifie que tous les fichiers sont présents
- ✅ Propose de lancer le projet automatiquement

**C'est le script à utiliser en premier !**

### 2. `setup-project.ps1` - Création de l'arborescence
**Utilisation :** `powershell -ExecutionPolicy Bypass -File setup-project.ps1`

Crée uniquement la structure de dossiers et les fichiers vides :
```
forge-agi/
  apps/ui/
  bricks/mobile_app_base/
  services/api/
  services/worker/
  infra/docker/
  specs/examples/
  specs/schema/
  .github/workflows/
```

### 3. `fill-files.ps1` - Remplissage des fichiers
**Utilisation :** `powershell -ExecutionPolicy Bypass -File fill-files.ps1`

Remplit tous les fichiers créés avec le contenu approprié :
- Dockerfiles (Flutter, API, Worker)
- docker-compose.yml
- GitHub Actions workflow
- README.md
- Spécifications et schémas
- Code Python (FastAPI + Celery)

### 4. `launch-project.ps1` - Lancement du projet
**Utilisation :** `powershell -ExecutionPolicy Bypass -File launch-project.ps1`

Lance le projet avec Docker Compose :
- ✅ Vérifie que Docker est installé
- ✅ Construit les images Docker
- ✅ Démarre tous les services
- ✅ Teste l'accessibilité de l'API

## Workflow recommandé

### Option 1 : Initialisation complète (RECOMMANDÉE)
```powershell
# Une seule commande pour tout faire
powershell -ExecutionPolicy Bypass -File init-project.ps1
```

### Option 2 : Étapes séparées
```powershell
# 1. Créer l'arborescence
powershell -ExecutionPolicy Bypass -File setup-project.ps1

# 2. Remplir les fichiers
powershell -ExecutionPolicy Bypass -File fill-files.ps1

# 3. Lancer le projet
powershell -ExecutionPolicy Bypass -File launch-project.ps1
```

## Services disponibles après lancement

Une fois le projet lancé, les services suivants sont disponibles :

| Service | URL | Description |
|---------|-----|-------------|
| API FastAPI | http://localhost:8000 | API principale |
| Documentation API | http://localhost:8000/docs | Documentation interactive |
| PostgreSQL | localhost:5432 | Base de données |
| Redis | localhost:6379 | Cache et message broker |

## Commandes Docker utiles

```powershell
# Voir le statut des services
docker-compose ps

# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down

# Redémarrer un service
docker-compose restart api

# Reconstruire les images
docker-compose build --no-cache
```

## Dépannage

### Problème : "Docker n'est pas installé"
**Solution :** Installer Docker Desktop depuis https://www.docker.com/products/docker-desktop

### Problème : "Ports déjà utilisés"
**Solution :** Vérifier qu'aucun autre service n'utilise les ports 8000, 5432, 6379

### Problème : "Permission denied"
**Solution :** Exécuter PowerShell en tant qu'administrateur

### Problème : "ExecutionPolicy"
**Solution :** Utiliser `-ExecutionPolicy Bypass` comme dans les exemples

## Structure finale du projet

```
forge-agi/
  apps/
    ui/                  # Dashboard Next.js (à venir)
  bricks/
    mobile_app_base/     # Mason brick Flutter
  services/
    api/                 # FastAPI
    worker/              # Celery worker
  infra/
    docker/
      Dockerfile.flutter
      Dockerfile.api
      Dockerfile.worker
    docker-compose.yml
  specs/
    examples/resa.yaml
    schema/mobile-app-0.1.0.json
  .github/workflows/build-apk.yml
  README.md
  SCRIPTS.md
```

## Prochaines étapes

1. **Tester l'API** : Accéder à http://localhost:8000/docs
2. **Créer une spécification** : Modifier `specs/examples/resa.yaml`
3. **Développer le dashboard** : Travailler dans `apps/ui/`
4. **Améliorer la génération** : Modifier `services/worker/main.py`

## Support

Pour toute question ou problème :
1. Consulter le README.md
2. Vérifier les logs Docker : `docker-compose logs`
3. Tester l'API : http://localhost:8000/health
