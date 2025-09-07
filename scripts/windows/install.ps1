# Install dependencies for local testing
# PowerShell version

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing MCP Server Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Cyan
Write-Host ""

# Upgrade pip
Write-Host "[1/3] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install MCP SDK
Write-Host ""
Write-Host "[2/3] Installing MCP SDK..." -ForegroundColor Yellow
pip install mcp[cli] --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ MCP SDK installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠ MCP SDK installation had issues" -ForegroundColor Yellow
}

# Install other requirements
Write-Host ""
Write-Host "[3/3] Installing other dependencies..." -ForegroundColor Yellow
pip install starlette uvicorn[standard] httpx python-dotenv aiofiles --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Some dependencies had issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing installation..." -ForegroundColor Cyan
Write-Host ""

# Test imports
python -c "from mcp.server import Server; print('  ✓ MCP SDK working')" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -c "from mcp import Server; print('  ✓ MCP SDK working (old structure)')" 2>$null
}

python -c "import starlette; print('  ✓ Starlette working')" 2>$null
python -c "import uvicorn; print('  ✓ Uvicorn working')" 2>$null

Write-Host ""
Write-Host "You can now:" -ForegroundColor Cyan
Write-Host "  Test locally:     python test_local.py" -ForegroundColor White
Write-Host "  Run server:       python src\remote_mcp\server.py" -ForegroundColor White
Write-Host "  Use Docker:       .\windows_setup.ps1" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
