# Script principal pour initialiser et lancer le projet forge-agi
# Auteur: Assistant IA

Write-Host "🎯 Initialisation complete du projet forge-agi" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Étape 1: Création de l'arborescence
Write-Host "`n📁 Etape 1: Creation de l'arborescence..." -ForegroundColor Blue
if (Test-Path "setup-project.ps1") {
    Write-Host "Execution de setup-project.ps1..." -ForegroundColor Cyan
    & powershell -ExecutionPolicy Bypass -File "setup-project.ps1"
} else {
    Write-Host "❌ Script setup-project.ps1 introuvable" -ForegroundColor Red
    exit 1
}

# Étape 2: Remplissage des fichiers
Write-Host "`n📄 Etape 2: Remplissage des fichiers..." -ForegroundColor Blue
if (Test-Path "fill-files.ps1") {
    Write-Host "Execution de fill-files.ps1..." -ForegroundColor Cyan
    & powershell -ExecutionPolicy Bypass -File "fill-files.ps1"
} else {
    Write-Host "❌ Script fill-files.ps1 introuvable" -ForegroundColor Red
    exit 1
}

# Étape 3: Vérification de la structure
Write-Host "`n🔍 Etape 3: Verification de la structure..." -ForegroundColor Blue
$requiredFiles = @(
    "infra/docker-compose.yml",
    "infra/docker/Dockerfile.api",
    "infra/docker/Dockerfile.worker",
    "infra/docker/Dockerfile.flutter",
    "services/api/main.py",
    "services/api/requirements.txt",
    "services/worker/main.py",
    "services/worker/requirements.txt",
    "specs/examples/resa.yaml",
    "specs/schema/mobile-app-0.1.0.json",
    "README.md"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Fichiers manquants:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "✅ Tous les fichiers requis sont presents" -ForegroundColor Green
}

# Étape 4: Demande de lancement
Write-Host "`n🚀 Etape 4: Lancement du projet..." -ForegroundColor Blue
$response = Read-Host "Voulez-vous lancer le projet maintenant? (o/n)"

if ($response -eq "o" -or $response -eq "O" -or $response -eq "oui" -or $response -eq "y" -or $response -eq "Y") {
    Write-Host "Lancement du projet..." -ForegroundColor Cyan
    if (Test-Path "launch-project.ps1") {
        & powershell -ExecutionPolicy Bypass -File "launch-project.ps1"
    } else {
        Write-Host "❌ Script launch-project.ps1 introuvable" -ForegroundColor Red
        Write-Host "Vous pouvez lancer manuellement avec: cd infra && docker-compose up -d" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n📋 Lancement manuel:" -ForegroundColor Yellow
    Write-Host "1. Naviguez vers le dossier infra: cd infra" -ForegroundColor White
    Write-Host "2. Lancez les services: docker-compose up -d" -ForegroundColor White
    Write-Host "3. Accedez a l'API: http://localhost:8000" -ForegroundColor White
}

Write-Host "`n🎉 Initialisation terminee!" -ForegroundColor Green
Write-Host "`n📚 Documentation:" -ForegroundColor Yellow
Write-Host "• README.md - Documentation generale" -ForegroundColor White
Write-Host "• specs/examples/resa.yaml - Exemple de specification" -ForegroundColor White
Write-Host "• http://localhost:8000/docs - Documentation API (apres lancement)" -ForegroundColor White

Write-Host "`n🔧 Scripts disponibles:" -ForegroundColor Yellow
Write-Host "• setup-project.ps1 - Creation de l'arborescence" -ForegroundColor White
Write-Host "• fill-files.ps1 - Remplissage des fichiers" -ForegroundColor White
Write-Host "• launch-project.ps1 - Lancement du projet" -ForegroundColor White
Write-Host "• init-project.ps1 - Ce script (initialisation complete)" -ForegroundColor White
