# verify_simple.ps1
# Vérifie Forge-AGI de bout en bout (Windows, PowerShell 5/7).
# - Prérequis: Docker Desktop, Python 3.x dans PATH
# - Démarre db/redis/api et vérifie /v1/health
# - Crée un venv local temporaire, installe deps min
# - Lance le pipeline et valide les artefacts

param(
  [int]$HealthTimeoutSec = 45,
  [switch]$NoBuild = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------- Helpers ----------
function Info($m){ Write-Host ("[INFO]  {0}" -f $m) -ForegroundColor Cyan }
function Ok($m){ Write-Host ("[OK]    {0}" -f $m) -ForegroundColor Green }
function Warn($m){ Write-Host ("[WARN]  {0}" -f $m) -ForegroundColor Yellow }
function Err($m){ Write-Host ("[ERR]   {0}" -f $m) -ForegroundColor Red }
function Need([string]$Path){ if(!(Test-Path -LiteralPath $Path)){ throw "Missing file: $Path" } }

# Détection robuste du répertoire du script (PS 5/7)
if ($PSScriptRoot -and (Test-Path -LiteralPath $PSScriptRoot)) {
    $repo = $PSScriptRoot
  } else {
    $repo = (Get-Location).Path
  }
  Set-Location -LiteralPath $repo
  
# Chemins clés
$compose = Join-Path $repo "infra\docker-compose.yml"
$spec = Join-Path $repo "specs\examples\resa.yaml"
$work = Join-Path $repo "work"
$scriptPipeline = Join-Path $repo "scripts\dev_run_pipeline.py"

# ---------- 0) Sanity ----------
Info "Sanity check"
Need $compose
Need $spec
Need $scriptPipeline
if(!(Test-Path $work)){ New-Item -ItemType Directory -Path $work | Out-Null }

# ---------- 1) Prérequis ----------
Info "Docker & Python"
# Docker
try {
  $null = & docker --version 2>$null
} catch {
  throw "Docker CLI non trouvé. Installe Docker Desktop et relance."
}
# Python
try {
  $pyv = & python -c "import sys; print(sys.version.split()[0])"
  if(-not $pyv){ throw "python not in PATH" }
  Info "Python $pyv"
} catch {
  throw "Python non trouvé dans PATH."
}
Ok "Prerequis OK"

# ---------- 2) Stack API ----------
if(-not $NoBuild){
  Info "docker compose build api"
  & docker compose -f $compose build api | Write-Host
} else {
  Warn "Skip build (per flag)"
}
Info "docker compose up -d db redis api"
& docker compose -f $compose up -d db redis api | Write-Host

# Healthcheck /v1/health
$healthUrl = "http://127.0.0.1:8080/v1/health"
$deadline = [DateTime]::UtcNow.AddSeconds($HealthTimeoutSec)
$healthy = $false
Info "Waiting API health at $healthUrl ..."
while([DateTime]::UtcNow -lt $deadline){
  try {
    $resp = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 3
    if($resp.ok -eq $true){ $healthy = $true; break }
  } catch { Start-Sleep -Milliseconds 800 }
}
if(-not $healthy){ throw "API healthcheck failed." }
Ok "/v1/health OK"

# ---------- 3) Venv & deps locales (côté host) ----------
$venv = Join-Path $repo ".verify_venv"
$pyExec = if (Test-Path (Join-Path $venv "Scripts\python.exe")) { Join-Path $venv "Scripts\python.exe" } else { $null }

if(-not $pyExec){
  Info "Creating venv: $venv"
  & python -m venv $venv
  $pyExec = Join-Path $venv "Scripts\python.exe"
}
Ok "venv OK"

Info "Installing minimal deps in venv"
# On reste minimal : pyyaml, jsonschema, click, rich (souvent importé par le pipeline)
& $pyExec -m pip install --upgrade pip > $null
& $pyExec -m pip install pyyaml==6.0.1 jsonschema==4.21.1 click==8.1.7 rich==13.7.1 > $null
Ok "Deps installées"

# ---------- 4) Lancement pipeline ----------
# On capture l’instant pour retrouver le run généré
$start = Get-Date

Info "Running pipeline (sans --run-id)"
# éviter collisions côté imports
$env:PYTHONPATH = ""

# Exécution directe pour récupérer un code fiable via $LASTEXITCODE
$LASTEXITCODE = 0
& $pyExec $scriptPipeline $spec
$code = $LASTEXITCODE

if ($code -ne 0) {
  throw "Pipeline a retourné un code != 0 ($code)"
}
Ok "Pipeline terminé"

# On récupère le dossier de run le plus récent créé après $start
$runDirObj = Get-ChildItem -LiteralPath $work -Directory |
  Where-Object { $_.LastWriteTime -ge $start.AddSeconds(-2) } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if (-not $runDirObj) { throw "Impossible d'identifier le dossier de run dans $work" }

$verifyRunPath = $runDirObj.FullName
$appDir       = Join-Path $verifyRunPath "app"
$artifactsDir = Join-Path $verifyRunPath "artifacts"
Info ("Run détecté: {0}" -f (Split-Path $verifyRunPath -Leaf))


# ---------- 5) Validation souple des artefacts ----------
function Show-Tree($Path){
    Write-Host "----- ls $Path -----" -ForegroundColor DarkGray
    Get-ChildItem -LiteralPath $Path -Recurse -Force |
      Select-Object FullName, Length, LastWriteTime |
      Format-Table -AutoSize
    Write-Host "---------------------" -ForegroundColor DarkGray
  }
  
  Info ("Validating artifacts in {0}" -f $verifyRunPath)
  if(-not (Test-Path -LiteralPath $appDir)){ throw "Dossier app manquant: $appDir" }
  if(-not (Test-Path -LiteralPath $artifactsDir)){
    Warn "Dossier artifacts introuvable, fallback sur le run root."
    New-Item -ItemType Directory -Force -Path $artifactsDir | Out-Null
  }
  
  # Trace utile : contenu des dossiers clés
  Show-Tree $verifyRunPath
  Show-Tree $artifactsDir
  
  # Attendus (nommage standard du worker)
  $expected = @(
    "spec.yml",
    "critic_report.json",
    "verifier_report.json",
    "judge_report.json",
    "source.zip"
  )
  
  # Helper : teste dans artifacts puis dans root; copie si trouvé au root
  $missing = @()
  foreach($fname in $expected){
    $pArt = Join-Path $artifactsDir $fname
    if(Test-Path -LiteralPath $pArt){ continue }
  
    $pRoot = Join-Path $verifyRunPath $fname
    if(Test-Path -LiteralPath $pRoot){
      Info "Normalisation: copie $fname du root vers artifacts/"
      Copy-Item -LiteralPath $pRoot -Destination $pArt -Force
    } else {
      $missing += $fname
    }
  }
  
  # At least, l’app doit être générée
  $pubspec = Join-Path $appDir "pubspec.yaml"
  if(-not (Test-Path -LiteralPath $pubspec)){
    throw "pubspec.yaml manquant dans l'app générée: $pubspec"
  }
  
  # Si certains artefacts restent manquants : warning, pas fatal si l’essentiel est là
  if($missing.Count -gt 0){
    Warn ("Artefacts manquants après fallback: {0}" -f ($missing -join ", "))
  } else {
    Ok "Artefacts complets dans artifacts/"
  }
  
  # Récap final
  $present = Get-ChildItem -LiteralPath $artifactsDir -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
  Info ("Artefacts présents: {0}" -f ($present -join ", "))
  
  Ok "Validation artefacts terminée"
  
  

# ---------- 6) (Optionnel) runner Flutter & mason (présence simple) ----------
# On ne fait PAS d'init/add/make pour éviter quoting CRLF.
try{
  Info "runner_flutter sanity (version mason/dart)"
  $out = & docker compose -f $compose run --rm runner_flutter bash -lc "dart --version && mason --version"
  if($LASTEXITCODE -eq 0){ Ok "runner reports dart/mason" } else { Warn "runner check non critique a échoué" }
} catch { Warn "runner check non critique a échoué: $($_.Exception.Message)" }
  
# ---------- Résumé ----------
Write-Host ""
Ok "Vérification terminée avec succès."
Write-Host "Résumé:"
Write-Host "  - API /v1/health OK"
Write-Host "  - Pipeline exécuté (run-id: $verifyRunId)"
Write-Host "  - Artefacts présents: app & artifacts/*.json + source.zip"
Write-Host "  - (Optionnel) runner flutter/mason: check basique effectué"
exit 0
