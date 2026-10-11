# Build script for VeTube
# Runs cxfreeze build and removes duplicate sound_lib DLLs
param([switch]$Msi)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot "bootstrap.exe") -PathType Leaf)) {
    throw "Missing prebuilt bootstrap.exe. Build it explicitly with ./native/bootstrap/build.ps1."
}

Write-Host "=== Building VeTube ===" -ForegroundColor Cyan

# Clean previous builds
foreach ($directory in @("build", "build2")) {
    $target = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $directory))
    $workspacePrefix = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
    if (-not $target.StartsWith($workspacePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Build cleanup escaped the repository"
    }
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
}

# Run cxfreeze build
uv run cxfreeze build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build FAILED" -ForegroundColor Red
    exit 1
}

# Remove duplicate sound_lib DLLs
# cx_Freeze copies sound_lib package to lib/sound_lib/ including the lib/ subdirectory with DLLs
# Our include_files already puts DLLs in sound_lib/lib/ (where paths.py expects them)
# So we remove the duplicate at lib/sound_lib/lib/
$buildPath = Get-ChildItem -LiteralPath "build" -Directory | Select-Object -First 1
$duplicatePath = [IO.Path]::GetFullPath((Join-Path $buildPath.FullName "lib/sound_lib/lib"))
if (-not $duplicatePath.StartsWith($workspacePrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Duplicate-library cleanup escaped the repository"
}
if (Test-Path -LiteralPath $duplicatePath) {
    Remove-Item -LiteralPath $duplicatePath -Recurse -Force
    Write-Host "Removed duplicate: $duplicatePath" -ForegroundColor Yellow
}

$buildPath = Get-ChildItem -LiteralPath "build" -Directory | Select-Object -First 1
if ($Msi) {
    uv run python tools/package_native.py $buildPath.FullName
} else {
    uv run python tools/package_native.py $buildPath.FullName --legacy-pyd
}
if ($LASTEXITCODE -ne 0) { throw "Native package preparation failed" }
if ($Msi) {
    uv run cxfreeze bdist_msi --skip-build
    if ($LASTEXITCODE -ne 0) { throw "MSI build failed" }
}

# Calculate final size
$size = (Get-ChildItem -Recurse build -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
$sizeMB = [math]::Round($size / 1MB, 2)
Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "Size: $sizeMB MB" -ForegroundColor Green
