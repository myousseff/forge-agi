# Script PowerShell pour lancer le projet forge-agi
# Auteur: Assistant IA

Write-Host "🚀 Lancement du projet forge-agi..." -ForegroundColor Green

# Vérifier si Docker est installé
try {
    docker --version | Out-Null
    Write-Host "✅ Docker detecte" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker n'est pas installe ou n'est pas accessible" -ForegroundColor Red
    Write-Host "Veuillez installer Docker Desktop et redemarrer votre terminal" -ForegroundColor Yellow
    exit 1
}

# Vérifier si Docker Compose est disponible
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose detecte" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose n'est pas disponible" -ForegroundColor Red
    Write-Host "Veuillez installer Docker Compose" -ForegroundColor Yellow
    exit 1
}

# Naviguer vers le dossier infra
Write-Host "📁 Navigation vers le dossier infra..." -ForegroundColor Blue
Set-Location "infra"

# Vérifier si le fichier docker-compose.yml existe
if (!(Test-Path "docker-compose.yml")) {
    Write-Host "❌ Fichier docker-compose.yml introuvable" -ForegroundColor Red
    Write-Host "Veuillez d'abord executer setup-project.ps1 et fill-files.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Fichier docker-compose.yml trouve" -ForegroundColor Green

# Construire et démarrer les services
Write-Host "🔨 Construction et demarrage des services..." -ForegroundColor Blue
Write-Host "Cela peut prendre quelques minutes lors de la premiere execution..." -ForegroundColor Yellow

try {
    # Construire les images
    Write-Host "📦 Construction des images Docker..." -ForegroundColor Cyan
    docker-compose build
    
    # Démarrer les services
    Write-Host "🚀 Demarrage des services..." -ForegroundColor Cyan
    docker-compose up -d
    
    Write-Host "`n🎉 Projet forge-agi lance avec succes!" -ForegroundColor Green
    Write-Host "`n📋 Services disponibles:" -ForegroundColor Yellow
    Write-Host "• API FastAPI: http://localhost:8000" -ForegroundColor White
    Write-Host "• Documentation API: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "• Base de donnees PostgreSQL: localhost:5432" -ForegroundColor White
    Write-Host "• Redis: localhost:6379" -ForegroundColor White
    
    Write-Host "`n🔍 Verification du statut des services..." -ForegroundColor Blue
    docker-compose ps
    
    Write-Host "`n📚 Commandes utiles:" -ForegroundColor Yellow
    Write-Host "• Voir les logs: docker-compose logs -f" -ForegroundColor White
    Write-Host "• Arreter les services: docker-compose down" -ForegroundColor White
    Write-Host "• Redemarrer un service: docker-compose restart [service_name]" -ForegroundColor White
    
    Write-Host "`n🌐 Test de l'API..." -ForegroundColor Blue
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
        Write-Host "✅ API accessible: $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  API pas encore accessible, veuillez attendre quelques secondes" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Erreur lors du lancement: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n🔧 Depannage:" -ForegroundColor Yellow
    Write-Host "1. Verifiez que Docker Desktop est en cours d'execution" -ForegroundColor White
    Write-Host "2. Verifiez que les ports 8000, 5432, 6379 sont disponibles" -ForegroundColor White
    Write-Host "3. Consultez les logs: docker-compose logs" -ForegroundColor White
}

Write-Host "`n📖 Pour plus d'informations, consultez le README.md" -ForegroundColor Cyan
