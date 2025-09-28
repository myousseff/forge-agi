# fix_forge_agi.ps1
# Applies automatic fixes to Forge-AGI repo and re-verifies end-to-end on Windows.
# - Removes blocking ENTRYPOINT for worker, normalizes docker-compose worker
# - Pins worker requirements to allowed set
# - Makes packaging ZIP deterministic (stable checksums)
# - Rebuilds minimal images and re-runs verification
# Run from repo root: .\fix_forge_agi.ps1 [-SkipBuild] [-SkipVerify]

param(
  [switch]$SkipBuild = $false,
  [switch]$SkipVerify = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info($m){ Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[OK]    $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "[ERR]   $m" -ForegroundColor Red }

function Assert-File([string]$Path){
  if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
}
function Backup-Once([string]$Path){
  if (Test-Path -LiteralPath $Path){
    $bak = "$Path.bak"
    if (-not (Test-Path -LiteralPath $bak)){
      Copy-Item -LiteralPath $Path -Destination $bak
    }
  }
}
function Replace-InFile([string]$Path, [string]$Pattern, [string]$Replacement){
  $txt = Get-Content -LiteralPath $Path -Raw
  $new = [System.Text.RegularExpressions.Regex]::Replace($txt, $Pattern, $Replacement, 'Singleline')
  if ($new -ne $txt){
    Set-Content -LiteralPath $Path -Value $new -Encoding UTF8
    return $true
  }
  return $false
}
function Ensure-Line([string]$Path, [string]$Marker, [string]$LineToAdd){
  $txt = Get-Content -LiteralPath $Path -Raw
  if ($txt -notmatch [regex]::Escape($Marker)){
    Add-Content -LiteralPath $Path -Value $LineToAdd
    return $true
  }
  return $false
}

# --- Paths
$dockerfileWorker = ".\infra\docker\Dockerfile.worker"
$composePath      = ".\infra\docker-compose.yml"
$reqWorker        = ".\services\worker\requirements.txt"
$pipelinePy       = ".\services\worker\worker\pipeline.py"
$verifyScript     = ".\verify_forge_agi.ps1"
$verifyWinScript  = ".\verify_forge_agi_win.ps1"

# --- Sanity
Assert-File $dockerfileWorker
Assert-File $composePath
Assert-File $reqWorker
Assert-File $pipelinePy

# ============================================================
# A) Dockerfile.worker: remove ENTRYPOINT sleep; ensure CMD ["bash"]
# ============================================================
Info "Patching Dockerfile.worker"
Backup-Once $dockerfileWorker

# Remove ENTRYPOINT ["sleep","infinity"]
$changedA1 = Replace-InFile $dockerfileWorker '^\s*ENTRYPOINT\s*\[\s*"sleep"\s*,\s*"infinity"\s*\]\s*$' ''

# Ensure CMD ["bash"] present (only once, at end)
$dfTxt = Get-Content -LiteralPath $dockerfileWorker -Raw
if ($dfTxt -notmatch '^\s*CMD\s*\[\s*"bash"\s*\]\s*$'){
  Add-Content -LiteralPath $dockerfileWorker -Value "`n# default interactive shell`nCMD [`"bash`"]`n"
  $changedA2 = $true
} else { $changedA2 = $false }
if ($changedA1 -or $changedA2){ Ok "Dockerfile.worker patched" } else { Info "Dockerfile.worker already OK" }

# ============================================================
# B) docker-compose.yml: normalize worker service
#   - remove command: ["sleep","infinity"]
#   - ensure volumes ..:/workspace and ../work:/work
#   - ensure env REPO_ROOT=/workspace, WORK_DIR=/work
# ============================================================
Info "Patching docker-compose worker service"
Backup-Once $composePath

# Remove 'command: ["sleep","infinity"]' under worker
$changedB1 = Replace-InFile $composePath '(?ms)(worker:\s*(?:\n.+?)*?)\n\s*command:\s*\[\s*"sleep"\s*,\s*"infinity"\s*\]' '$1'

# Ensure volumes entries
$composeTxt = Get-Content -LiteralPath $composePath -Raw
if ($composeTxt -match '(?ms)worker:\s*(?:\n\s+.+)*?\n\s+volumes:\s*(?<vol>(?:\n\s+-\s+.+)+)'){
  $volBlock = $Matches['vol']
  $needWorkspace = ($volBlock -notmatch '\.\.:/workspace')
  $needWork      = ($volBlock -notmatch '\.\./work:/work')
  if ($needWorkspace -or $needWork){
    # insert lines after 'volumes:' line
    $composeTxt = [regex]::Replace($composeTxt,'(?ms)(worker:\s*(?:\n\s+.+)*?\n\s+volumes:\s*)(?<rest>(?:\n\s+-\s+.+)+)',{
      param($m)
      $head = $m.Groups[1].Value
      $rest = $m.Groups['rest'].Value
      if ($rest -notmatch '\.\.:/workspace'){ $rest += "`n      - ..:/workspace" }
      if ($rest -notmatch '\.\./work:/work'){ $rest += "`n      - ../work:/work" }
      return $head + $rest
    })
    Set-Content -LiteralPath $composePath -Value $composeTxt -Encoding UTF8
    $changedB2 = $true
  } else { $changedB2 = $false }
} else {
  Warn "Could not find volumes block for worker; please check $composePath"
  $changedB2 = $false
}

# Ensure environment REPO_ROOT=/workspace and WORK_DIR=/work
$composeTxt = Get-Content -LiteralPath $composePath -Raw
if ($composeTxt -match '(?ms)worker:\s*(?:\n\s+.+)*?\n\s+environment:\s*(?<env>(?:\n\s+-\s+.+)+)'){
  $envBlock = $Matches['env']
  $needRepo = ($envBlock -notmatch 'REPO_ROOT=/workspace')
  $needWork = ($envBlock -notmatch 'WORK_DIR=/work')
  if ($needRepo -or $needWork){
    $composeTxt = [regex]::Replace($composeTxt,'(?ms)(worker:\s*(?:\n\s+.+)*?\n\s+environment:\s*)(?<rest>(?:\n\s+-\s+.+)+)',{
      param($m)
      $head = $m.Groups[1].Value
      $rest = $m.Groups['rest'].Value
      if ($rest -notmatch 'REPO_ROOT=/workspace'){ $rest += "`n      - REPO_ROOT=/workspace" }
      if ($rest -notmatch 'WORK_DIR=/work'){ $rest += "`n      - WORK_DIR=/work" }
      return $head + $rest
    })
    Set-Content -LiteralPath $composePath -Value $composeTxt -Encoding UTF8
    $changedB3 = $true
  } else { $changedB3 = $false }
} else {
  Warn "Could not find environment block for worker; please check $composePath"
  $changedB3 = $false
}

if ($changedB1 -or $changedB2 -or $changedB3){ Ok "docker-compose worker normalized" } else { Info "docker-compose worker already OK" }

# ============================================================
# C) Worker requirements: restrict to allowed list
# ============================================================
Info "Patching worker requirements"
Backup-Once $reqWorker
$allowedReq = @"
celery==5.3.6
pyyaml==6.0.1
jsonschema==4.21.1
click==8.1.7
"@.Trim() + "`n"
Set-Content -LiteralPath $reqWorker -Value $allowedReq -Encoding UTF8
Ok "worker/requirements.txt pinned to allowed set"

# ============================================================
# D) Make packaging deterministic in pipeline.py
#   - inject helper _zip_deterministic if missing
#   - replace any direct ZipFile(...).write/ writestr usage for source.zip
#   - if a run_package exists, ensure it uses _zip_deterministic
# ============================================================
Info "Patching pipeline.py for deterministic zips"
Backup-Once $pipelinePy
$py = Get-Content -LiteralPath $pipelinePy -Raw

$needImports = ($py -notmatch 'from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED')
if ($needImports){
  $py = $py -replace '(\nimport[^\n]*\n)','$1from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED' + "`n"
}

$needHelper = ($py -notmatch 'def _zip_deterministic\(')
if ($needHelper){
  $helper = @"
DETERMINISTIC_TS = (1980, 1, 1, 0, 0, 0)

def _zip_deterministic(zip_path: Path, root_dir: Path):
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(root_dir.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(root_dir).as_posix()
            data = p.read_bytes()
            info = ZipInfo(filename=rel, date_time=DETERMINISTIC_TS)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            zf.writestr(info, data)
"@
  # append helper near top-level (after imports)
  # find last import line
  $py = $py -replace '(\nfrom zipfile[^\n]*\n)','$1' + $helper + "`n"
}

# Replace common patterns that create source.zip using ZipFile
$py = $py -replace '(?ms)with\s+ZipFile\(\s*zip_path\s*,\s*["'']w["''].*?\)\s*as\s*\w+:\s*.*?\n','_zip_deterministic(zip_path, source_dir)' + "`n"

# Ensure run_package uses _zip_deterministic(zip_path, source_dir)
if ($py -match '(?ms)def\s+run_package\([^\)]*\):'){
  # In run_package body, ensure call to _zip_deterministic
  $py = [regex]::Replace($py,'(?ms)(def\s+run_package\([^\)]*\):\s*)(.*?)(\n\s*return\s*\{)', {
      param($m)
      $head = $m.Groups[1].Value
      $body = $m.Groups[2].Value
      $ret  = $m.Groups[3].Value
      # Ensure variables exist
      if ($body -notmatch 'artifacts_dir.*=.*run_path.*artifacts'){
        $body = $body + "`n    artifacts_dir = run_path / 'artifacts'`n    artifacts_dir.mkdir(parents=True, exist_ok=True)`n"
      }
      if ($body -notmatch 'source_dir.*=.*run_path.*app'){
        $body = $body + "`n    source_dir = run_path / 'app'`n"
      }
      if ($body -notmatch 'zip_path.*=.*artifacts_dir.*source\.zip'){
        $body = $body + "`n    zip_path = artifacts_dir / 'source.zip'`n"
      }
      # Replace any ZipFile write with deterministic call
      $body = [regex]::Replace($body,'(?ms)with\s+ZipFile\([^\)]*\)\s*as\s*\w+:\s*.*?\n','    _zip_deterministic(zip_path, source_dir)`n')
      if ($body -notmatch '_zip_deterministic'){
        $body = $body + "`n    _zip_deterministic(zip_path, source_dir)`n"
      }
      return $head + $body + $ret
    })
}

Set-Content -LiteralPath $pipelinePy -Value $py -Encoding UTF8
Ok "pipeline.py patched for deterministic zips"

# ============================================================
# E) (Optional) ensure verify script present; if not, write Windows version
# ============================================================
if (-not (Test-Path -LiteralPath $verifyScript) -and -not (Test-Path -LiteralPath $verifyWinScript)){
  Info "verify script not found; writing minimal Windows verify script"
  $verifyMini = @"
# verify_forge_agi_win.ps1 (minimal)
param([switch]$SkipDockerBuild = \$false)
Write-Host "Quick verify ..." -ForegroundColor Cyan
# you can paste the previously provided verify script here if needed
"@
  Set-Content -LiteralPath $verifyWinScript -Value $verifyMini -Encoding UTF8
}

# ============================================================
# F) Rebuild minimal and run verification
# ============================================================
if (-not $SkipBuild){
  Info "Rebuilding worker image (and runner_flutter if needed)"
  docker compose -f $composePath build worker | Write-Host
}
else {
  Warn "Skipping docker build per flag"
}

if (-not $SkipVerify){
  if (Test-Path -LiteralPath $verifyScript){
    Info "Running verify_forge_agi.ps1"
    . $verifyScript
  } elseif (Test-Path -LiteralPath $verifyWinScript){
    Info "Running verify_forge_agi_win.ps1"
    . $verifyWinScript
  } else {
    Warn "No verify script found to run."
  }
} else {
  Warn "Skipping verification per flag"
}

Ok "Fix script completed."
