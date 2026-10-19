param(
    [switch]$Clean,
    # Python launcher to use; the release workflow passes 'python' (actions/setup-python).
    [string]$Python = 'py'
)

$ErrorActionPreference = 'Stop'

if ($Clean) {
    Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
}

& $Python -m pip install -r requirements.txt
& $Python -m pip install pyinstaller
& $Python -m PyInstaller --clean --noconfirm EdgeVoiceTTS.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

$manifest = Get-Content (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$version = if ($manifest.version) { [string]$manifest.version } else { '0.0.0' }
$dist = Join-Path $PSScriptRoot 'dist'
$exePath = Join-Path $dist 'EdgeVoiceTTS.exe'

# The voices catalog is taken from the live service at build time.
& $exePath --export-voices-json (Join-Path $dist 'voices.json')
if ($LASTEXITCODE -ne 0) { throw "Exporting the voices catalog failed" }

Copy-Item (Join-Path $PSScriptRoot 'manifest.json') $dist -Force
Copy-Item (Join-Path $PSScriptRoot 'README.md') $dist -Force
Copy-Item (Join-Path $PSScriptRoot 'LICENSE') (Join-Path $dist 'LICENSE.txt') -Force
Copy-Item (Join-Path $PSScriptRoot 'LICENSE.edge-tts.txt') $dist -Force

$zipPath = Join-Path $dist "EdgeVoiceTTS-$version.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

Push-Location $dist
try {
    Compress-Archive -Path @(
        'EdgeVoiceTTS.exe',
        'voices.json',
        'manifest.json',
        'README.md',
        'LICENSE.txt',
        'LICENSE.edge-tts.txt'
    ) -DestinationPath $zipPath -CompressionLevel Optimal
} finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Plugin zip:' $zipPath
