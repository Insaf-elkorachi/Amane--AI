param(
  [int]$Port = 8010
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  Write-Host "Environnement Python introuvable: $Python" -ForegroundColor Red
  Write-Host "Installe d'abord les dependances:" -ForegroundColor Yellow
  Write-Host "cd `"$Backend`""
  Write-Host "python -m venv .venv"
  Write-Host ".\.venv\Scripts\Activate.ps1"
  Write-Host "pip install -r requirements.txt"
  exit 1
}

function Get-AmaneLanIp {
  try {
    $config = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.IPv4Address.IPAddress -notlike "169.*" } | Select-Object -First 1
    if ($config -and $config.IPv4Address) { return $config.IPv4Address.IPAddress }
  } catch {}
  return "127.0.0.1"
}

$Ip = Get-AmaneLanIp
$LocalUrl = "http://127.0.0.1:$Port/app/"
$QrUrl = "http://127.0.0.1:$Port/qr"
$PhoneUrl = "http://$Ip`:$Port/app/"

Write-Host "AMANE local" -ForegroundColor Cyan
Write-Host "Assistant PC      : $LocalUrl"
Write-Host "QR PC             : $QrUrl"
Write-Host "Telephone Wi-Fi   : $PhoneUrl"
Write-Host "Note telephone    : le micro mobile demande souvent HTTPS. Utilise start_amane_ngrok.ps1 pour HTTPS." -ForegroundColor Yellow
Write-Host ""
Write-Host "Serveur lance. Ne ferme pas cette fenetre tant que tu utilises AMANE." -ForegroundColor Green

Set-Location $Backend
& $Python -m uvicorn main:app --reload --host 0.0.0.0 --port $Port
