param(
  [int]$Port = 8010
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  Write-Host "Environnement Python introuvable: $Python" -ForegroundColor Red
  exit 1
}

$NgrokCmd = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $NgrokCmd) {
  Write-Host "ngrok n'est pas installe ou pas dans le PATH." -ForegroundColor Red
  Write-Host "Installe ngrok, connecte ton authtoken, puis relance ce script." -ForegroundColor Yellow
  exit 1
}

Write-Host "Demarrage AMANE backend sur le port $Port..." -ForegroundColor Cyan
$BackendProcess = Start-Process powershell -PassThru -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy", "Bypass",
  "-Command", "cd '$Backend'; & '$Python' -m uvicorn main:app --reload --host 0.0.0.0 --port $Port"
)

Start-Sleep -Seconds 3
Write-Host "Demarrage ngrok HTTPS..." -ForegroundColor Cyan
$NgrokProcess = Start-Process ngrok -PassThru -ArgumentList @("http", "$Port")

$PublicUrl = $null
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try {
    $tunnels = Invoke-RestMethod "http://127.0.0.1:4040/api/tunnels"
    $PublicUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
    if ($PublicUrl) { break }
  } catch {}
}

if (-not $PublicUrl) {
  Write-Host "Impossible de lire l'URL ngrok. Ouvre http://127.0.0.1:4040 et copie l'URL HTTPS." -ForegroundColor Yellow
  exit 1
}

$AppUrl = "$PublicUrl/app/"
$QrUrl = "http://127.0.0.1:$Port/qr?target=$([uri]::EscapeDataString($AppUrl))"

Write-Host ""
Write-Host "AMANE est pret pour telephone" -ForegroundColor Green
Write-Host "URL HTTPS assistant : $AppUrl"
Write-Host "Page QR locale      : $QrUrl"
Write-Host ""
Write-Host "Important: sur ngrok gratuit, cette URL change a chaque relance. Pour un QR permanent, il faut un domaine ngrok reserve ou deployer en cloud." -ForegroundColor Yellow
Start-Process $QrUrl
