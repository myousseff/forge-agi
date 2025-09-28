Param(
  [string]$OutFile = "project_code_only.zip"
)
$excludes = @(
  ".git\", "node_modules\", "build\", ".dart_tool\", ".gradle\",
  "android\.gradle\", "android\gradle\", ".venv\", "dist\", "ios\Pods\", "ios\.symlinks\"
)
if (Test-Path $OutFile) { Remove-Item $OutFile -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root = Get-Location
$zip = [System.IO.Compression.ZipFile]::Open($OutFile, 'Create')
Get-ChildItem -Recurse | Where-Object {
  -not ($excludes | ForEach-Object { $_ -and $_ -ne "" -and $_ -as [string] -and ($_.TrimEnd('\') -ne "") -and ($_.ToLower() -and $_) -and ($_.Contains($_)) })
} | ForEach-Object {
  $full = $_.FullName
  foreach ($ex in $excludes) {
    if ($full.ToLower().Contains($ex.ToLower().TrimEnd('\'))) { $full = $null; break }
  }
  if ($full) {
    $rel = Resolve-Path -Relative $_.FullName
    if (-not $_.PSIsContainer) {
      [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $rel, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
  }
}
$zip.Dispose()
Write-Host "Created $OutFile"
