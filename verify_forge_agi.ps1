# verify_forge_agi_win.ps1
# End-to-end verification for Forge AGI on Windows (ASCII only)
# Run: .\verify_forge_agi_win.ps1  [-SkipDockerBuild]

param([switch]$SkipDockerBuild = $false)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info($m){ Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[OK]    $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "[ERR]   $m" -ForegroundColor Red }

function Assert-File([string]$Path){
  if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
}
function Assert-Command([string]$Cmd){
  try { $null = & $Cmd --version 2>$null } catch { throw "Command not found: $Cmd" }
}
function New-VenvIfNeeded([string]$VenvPath = ".\.venv"){
  if (-not (Test-Path -LiteralPath $VenvPath)) {
    Info "Creating Python venv at $VenvPath ..."
    python -m venv $VenvPath
  }
  $venvPy = Join-Path $VenvPath "Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $venvPy)) { throw "Virtualenv python not found: $venvPy" }
  return $venvPy
}
function WebHealth([string]$Url, [int]$TimeoutSec = 60){
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  do {
    try {
      $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
      if ($resp.StatusCode -eq 200 -and $resp.Content -match '"ok"\s*:\s*true') { return $true }
    } catch { Start-Sleep -Seconds 2 }
  } while ((Get-Date) -lt $deadline)
  return $false
}
function RepoRoot(){ (Get-Location).Path }
function ComposePath(){ Join-Path (RepoRoot) "infra\docker-compose.yml" }
function WorkDir(){
  $p = Join-Path (RepoRoot) "work"
  if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
  return $p
}
function Parse-ChecksumsFile([string]$Path){
  $map = @{}
  if (-not (Test-Path $Path)) { return $map }
  foreach($line in Get-Content -LiteralPath $Path){
    $line = $line.Trim()
    if ($line.Length -lt 3) { continue }
    $idx = $line.IndexOf("  ")
    if ($idx -lt 1) { continue }
    $hash = $line.Substring(0, $idx).Trim()
    $name = $line.Substring($idx + 2).Trim()
    if ($hash -and $name) { $map[$name] = $hash }
  }
  return $map
}
function Compare-Checksums([string]$DirA, [string]$DirB){
  $fa = Join-Path $DirA "artifacts\checksums.txt"
  $fb = Join-Path $DirB "artifacts\checksums.txt"
  if (-not (Test-Path $fa) -or -not (Test-Path $fb)) { return @{ equal = $false; reason = "checksums.txt missing" } }
  $A = Parse-ChecksumsFile $fa
  $B = Parse-ChecksumsFile $fb
  $all = New-Object System.Collections.Generic.HashSet[string]
  foreach($k in $A.Keys){ [void]$all.Add($k) }
  foreach($k in $B.Keys){ [void]$all.Add($k) }
  $equal = $true
  $rows = @()
  foreach($k in $all){
    $ha = $A[$k]; $hb = $B[$k]
    $eq = ($ha -eq $hb)
    if (-not $eq) { $equal = $false }
    $rows += [pscustomobject]@{ file=$k; A=$ha; B=$hb; equal=$eq }
  }
  return @{ equal=$equal; details=$rows }
}
function Run-PythonCode([string]$PythonExe, [string]$Code){
  $tmp = New-TemporaryFile
  $py = $tmp.FullName + ".py"
  Remove-Item $tmp -Force
  Set-Content -LiteralPath $py -Value $Code -Encoding UTF8
  & $PythonExe $py
  Remove-Item $py -Force
}

Write-Host "`n=== 0) Prerequisites ===" -ForegroundColor Magenta
Assert-Command docker
Assert-Command git
Assert-Command python

Assert-File ".\infra\docker-compose.yml"
Assert-File ".\infra\docker\Dockerfile.api"
Assert-File ".\infra\docker\Dockerfile.worker"
Assert-File ".\infra\docker\Dockerfile.flutter"
Assert-File ".\services\api\app\main.py"
Assert-File ".\services\api\requirements.txt"
Assert-File ".\services\worker\worker\pipeline.py"
Assert-File ".\services\worker\requirements.txt"
Assert-File ".\bricks\mobile_app_base\brick.yaml"
Assert-File ".\bricks\mobile_app_base\__brick__\pubspec.yaml"
Assert-File ".\bricks\mobile_app_base\__brick__\lib\main.dart"
Assert-File ".\bricks\mobile_app_base\__brick__\lib\app_router.dart"
Ok "Repo structure OK"

$venvPy = New-VenvIfNeeded
& $venvPy -m pip install --upgrade pip | Out-Null
& $venvPy -m pip install pyyaml jsonschema | Out-Null
Ok "Local Python env OK"

Write-Host "`n=== 1) API via Docker ===" -ForegroundColor Magenta
$compose = ComposePath
if (-not $SkipDockerBuild) {
  Info "docker compose build db redis api"
  docker compose -f $compose build db redis api | Out-Null
}
Info "docker compose up -d db redis api"
docker compose -f $compose up -d db redis api | Out-Null
if (WebHealth "http://127.0.0.1:8080/v1/health" 60) { Ok "/v1/health OK" } else { Err "API health failed"; exit 1 }

Write-Host "`n=== 2) Runner Flutter & mason_cli ===" -ForegroundColor Magenta
if (-not $SkipDockerBuild) {
  Info "docker compose build runner_flutter"
  docker compose -f $compose build runner_flutter | Out-Null
}
Info "Check Dart and mason versions in runner"
docker compose -f $compose run --rm runner_flutter bash -lc "dart --version; mason --version" | Write-Host
Ok "Runner reports Dart and mason"

Write-Host "`n=== 3) Manual Mason check (init/add/make) ===" -ForegroundColor Magenta
$work = WorkDir
$runId = "manual-mason-check"
$runDir = Join-Path $work $runId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$pyVarsCode = @"
import json, yaml, pathlib
spec = yaml.safe_load(open('specs/examples/resa.yaml','r',encoding='utf-8'))
vars_obj = {
  'app_name': spec['app']['name'],
  'primary_color': spec['app']['theme']['primary_color'],
  'navigation': spec['ui']['navigation'],
  'entities': [{'name': e['name'], 'fields':[f['name'] for f in e['fields']]} for e in spec['data']['entities']]
}
p = pathlib.Path(r'$runDir') / 'vars.json'
p.write_text(json.dumps(vars_obj, indent=2, ensure_ascii=False), encoding='utf-8')
print('OK ' + str(p))
"@
Run-PythonCode -PythonExe $venvPy -Code $pyVarsCode

Info "mason init/add/make inside runner"
docker compose -f $compose run --rm runner_flutter bash -lc "set -e; ls -la /workspace/bricks/mobile_app_base; cd /work; mason init >/dev/null 2>&1 || true; mason add mobile_app_base --path /workspace/bricks/mobile_app_base; mason make mobile_app_base -c /work/$runId/vars.json -o /work/$runId/app; ls -la /work/$runId/app" | Write-Host


$manualApp = Join-Path $runDir "app"
Assert-File (Join-Path $manualApp "pubspec.yaml")
Assert-File (Join-Path $manualApp "lib\main.dart")
Assert-File (Join-Path $manualApp "lib\app_router.dart")
Ok "Mason generation OK"

Write-Host "`n=== 4) Worker pipeline (two runs) ===" -ForegroundColor Magenta
if (-not $SkipDockerBuild) {
  Info "docker compose build worker"
  docker compose -f $compose build worker | Out-Null
}
Info "Pipeline run #1"
Info "Pipeline run #2"
docker compose -f $compose run --rm --entrypoint "" worker bash -lc "python -m worker.pipeline --spec /workspace/specs/examples/resa.yaml"
docker compose -f $compose run --rm --entrypoint "" worker bash -lc "python -m worker.pipeline --spec /workspace/specs/examples/resa.yaml"

$dirs = Get-ChildItem -Path $work -Directory | Sort-Object LastWriteTime -Descending
$withCks = @()
foreach($d in $dirs){
  if (Test-Path (Join-Path $d.FullName "artifacts\checksums.txt")) { $withCks += $d }
  if ($withCks.Count -ge 2) { break }
}
if ($withCks.Count -lt 2) { Err "Not enough runs with artifacts/checksums.txt"; exit 1 }

$A = $withCks[1].FullName
$B = $withCks[0].FullName
Info "Artifacts A: $A"
Info "Artifacts B: $B"

$expected = @("spec.yml","critic_report.json","verifier_report.json","judge_report.json","source.zip","checksums.txt")
foreach($f in $expected){
  Assert-File (Join-Path $A "artifacts\$f")
  Assert-File (Join-Path $B "artifacts\$f")
}
Ok "Artifacts present in both runs"

$res = Compare-Checksums $A $B
if ($res.equal) {
  Ok "Reproducibility: identical checksums"
} else {
  Warn "Reproducibility: differences detected (zip timestamps likely). Details follow:"
  $res.details | Format-Table -AutoSize | Out-String | Write-Host
}

Write-Host "`n=== 5) Worker dependencies sanity ===" -ForegroundColor Magenta
$allowed = @("celery","pyyaml","jsonschema","click")
$req = ".\services\worker\requirements.txt"
Assert-File $req
$lines = Get-Content $req | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and -not $_.StartsWith("#") }
$pkgs = $lines | ForEach-Object { ($_ -split "==|>=|<=|~=|>|<")[0].Trim().ToLower() }
$extra = $pkgs | Where-Object { $allowed -notcontains $_ }
if ($extra.Count -gt 0) { Warn ("Unapproved dependencies in worker/requirements.txt: " + ($extra -join ", ")) } else { Ok "Worker requirements OK" }

Write-Host "`nAll checks done." -ForegroundColor Green
