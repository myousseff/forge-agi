# Script PowerShell pour créer l'arborescence du projet forge-agi
# Auteur: Assistant IA

Write-Host "Creation de l'arborescence du projet forge-agi..." -ForegroundColor Green

# Fonction pour créer un dossier s'il n'existe pas
function Create-DirectoryIfNotExists {
    param([string]$Path)
    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "Cree: $Path" -ForegroundColor Cyan
    } else {
        Write-Host "Existe deja: $Path" -ForegroundColor Yellow
    }
}

# Fonction pour créer un fichier vide
function Create-EmptyFile {
    param([string]$Path)
    if (!(Test-Path $Path)) {
        New-Item -ItemType File -Path $Path -Force | Out-Null
        Write-Host "Cree: $Path" -ForegroundColor Cyan
    } else {
        Write-Host "Existe deja: $Path" -ForegroundColor Yellow
    }
}

# Création de l'arborescence des dossiers
Write-Host "Creation des dossiers..." -ForegroundColor Blue

# Apps
Create-DirectoryIfNotExists "apps/ui"

# Bricks
Create-DirectoryIfNotExists "bricks/mobile_app_base"

# Services
Create-DirectoryIfNotExists "services/api"
Create-DirectoryIfNotExists "services/worker"

# Infrastructure
Create-DirectoryIfNotExists "infra/docker"

# Specs
Create-DirectoryIfNotExists "specs/examples"
Create-DirectoryIfNotExists "specs/schema"

# GitHub workflows
Create-DirectoryIfNotExists ".github/workflows"

Write-Host "Creation des fichiers..." -ForegroundColor Blue

# Créer les fichiers vides d'abord
Create-EmptyFile "infra/docker/Dockerfile.flutter"
Create-EmptyFile "infra/docker/Dockerfile.api"
Create-EmptyFile "infra/docker/Dockerfile.worker"
Create-EmptyFile "infra/docker-compose.yml"
Create-EmptyFile ".github/workflows/build-apk.yml"
Create-EmptyFile "README.md"
Create-EmptyFile "specs/schema/mobile-app-0.1.0.json"
Create-EmptyFile "specs/examples/resa.yaml"
Create-EmptyFile "services/api/requirements.txt"
Create-EmptyFile "services/worker/requirements.txt"
Create-EmptyFile "services/api/main.py"
Create-EmptyFile "services/worker/main.py"

Write-Host "`nArborescence de base creee avec succes!" -ForegroundColor Green
Write-Host "`nProchaines etapes:" -ForegroundColor Yellow
Write-Host "1. Les fichiers ont ete crees vides" -ForegroundColor White
Write-Host "2. Vous pouvez maintenant les remplir avec le contenu approprie" -ForegroundColor White
Write-Host "3. Pour lancer le projet, naviguez vers infra et utilisez docker-compose" -ForegroundColor White
Write-Host "`nConsultez le README.md pour plus d'informations" -ForegroundColor Cyan
