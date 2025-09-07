# Build Docker image for Atlas Remote MCP
# PowerShell version

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Building Atlas Remote MCP Docker Image" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Navigate to project root (v2) - script is in v2\scripts\windows\
Set-Location "$ScriptDir\..\.."

Write-Host "Building from: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Function to test Docker build
function Test-DockerBuild {
    param(
        [string]$DockerfilePath,
        [string]$Description
    )
    
    Write-Host "Trying: $Description" -ForegroundColor Yellow
    $result = docker build -f $DockerfilePath -t atlas-remote-mcp:v2 . 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SUCCESS: $Description worked!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Failed: $Description" -ForegroundColor Red
        return $false
    }
}

# Step 1: Clean up
Write-Host "[1/3] Cleaning up Docker..." -ForegroundColor Cyan
docker system prune -f 2>&1 | Out-Null
docker rmi atlas-remote-mcp:v2 2>&1 | Out-Null
Write-Host "  ✓ Cleanup complete" -ForegroundColor Green

# Step 2: Try standard Dockerfile
Write-Host ""
Write-Host "[2/3] Building Docker image..." -ForegroundColor Cyan
if (Test-DockerBuild "deploy\docker\Dockerfile" "Standard Dockerfile") {
    Write-Host ""
    Write-Host "Build successful! You can now run:" -ForegroundColor Green
    Write-Host "  cd deploy\docker" -ForegroundColor White
    Write-Host "  docker-compose up" -ForegroundColor White
    Write-Host ""
    Write-Host "Or for HTTPS:" -ForegroundColor Gray
    Write-Host "  cd deploy\ssl\self-signed-working" -ForegroundColor White
    Write-Host "  .\start_https.bat" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 0
}

# Step 3: Try with minimal requirements
Write-Host ""
Write-Host "[3/3] Build failed. Trying with minimal requirements..." -ForegroundColor Cyan

$minimalRequirements = @"
fastmcp
starlette
uvicorn[standard]
python-dotenv
"@

# Backup original requirements
if (Test-Path "requirements.txt") {
    Copy-Item "requirements.txt" "requirements-backup.txt" -Force
}

# Write minimal requirements
$minimalRequirements | Out-File -FilePath "requirements-minimal.txt" -Encoding ASCII
Copy-Item "requirements-minimal.txt" "requirements.txt" -Force

Write-Host "  ✓ Created minimal requirements" -ForegroundColor Green

if (Test-DockerBuild "deploy\docker\Dockerfile" "Minimal requirements") {
    Write-Host ""
    Write-Host "Build successful with minimal requirements!" -ForegroundColor Green
    
    # Restore original requirements
    if (Test-Path "requirements-backup.txt") {
        Copy-Item "requirements-backup.txt" "requirements.txt" -Force
        Remove-Item "requirements-backup.txt"
        Remove-Item "requirements-minimal.txt"
    }
    
    Read-Host "Press Enter to exit"
    exit 0
}

# Restore original requirements
if (Test-Path "requirements-backup.txt") {
    Copy-Item "requirements-backup.txt" "requirements.txt" -Force
    Remove-Item "requirements-backup.txt"
    Remove-Item "requirements-minimal.txt" 2>$null
}

# Manual fix suggestions
Write-Host ""
Write-Host "Build failed. Please check:" -ForegroundColor Red
Write-Host "  1. Docker Desktop is running" -ForegroundColor Yellow
Write-Host "  2. Internet connection is working" -ForegroundColor Yellow
Write-Host "  3. Try: docker pull python:3.11-slim" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"
