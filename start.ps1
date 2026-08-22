# AERIX - Quick Start Script
# Run this script to start the AERIX Aerial Traffic Intelligence Backend

Write-Host "============================================================" -ForegroundColor Green
Write-Host "AERIX — Autonomous Aerial Traffic Intelligence Platform" -ForegroundColor Green  
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Check MongoDB connection
Write-Host "[1/2] Checking MongoDB connection..." -ForegroundColor Yellow
$mongoCheck = python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1.0)
res = s.connect_ex(('127.0.0.1', 27017))
s.close()
if res == 0:
    print('CONNECTED')
else:
    print('OFFLINE')
"

if ($mongoCheck -eq "CONNECTED") {
    Write-Host "[OK] MongoDB is running on port 27017" -ForegroundColor Green
} else {
    Write-Host "[WARN] MongoDB is not detected on port 27017. AERIX will run in local file-cache mode." -ForegroundColor Yellow
}

# Start AERIX Backend
Write-Host ""
Write-Host "[2/2] Starting AERIX FastAPI Backend..." -ForegroundColor Yellow
Write-Host "  * API Base URL : http://localhost:8000" -ForegroundColor Cyan
Write-Host "  * Swagger Docs : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  * Live Dashboard: http://localhost:8000/" -ForegroundColor Cyan
Write-Host ""

$env:PYTHONPATH = "."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload