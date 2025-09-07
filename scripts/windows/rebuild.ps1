# Quick rebuild script to fix current issues
# PowerShell version

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Quick Fix and Rebuild" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop all containers
Write-Host "[1/5] Stopping containers..." -ForegroundColor Yellow
docker-compose -f docker\docker-compose.https.yml down 2>$null
docker-compose -f docker\docker-compose.yml down 2>$null

# Step 2: Remove old images
Write-Host "[2/5] Removing old images..." -ForegroundColor Yellow
docker rmi atlas-remote-mcp:v2 2>$null

# Step 3: Clear cache
Write-Host "[3/5] Clearing Docker cache..." -ForegroundColor Yellow
docker builder prune -f 2>$null

# Step 4: Rebuild with no cache
Write-Host "[4/5] Building fresh image..." -ForegroundColor Yellow
Write-Host "  This will take a few minutes..." -ForegroundColor Gray

$buildResult = docker build --no-cache -f docker\Dockerfile.simple -t atlas-remote-mcp:v2 . 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Trying alternative approach..." -ForegroundColor Yellow
    
    # Try with even simpler approach
    Write-Host "Creating minimal Dockerfile..." -ForegroundColor Yellow
    
    $minimalDockerfile = @"
FROM python:3.11-slim
WORKDIR /app
RUN pip install mcp[cli] starlette uvicorn[standard] httpx python-dotenv aiofiles
COPY src/ ./src/
ENV PYTHONPATH=/app/src HOST=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["python", "/app/src/remote_mcp/server.py"]
"@
    
    $minimalDockerfile | Out-File -FilePath "docker\Dockerfile.minimal" -Encoding ASCII
    
    Write-Host "Building with minimal Dockerfile..." -ForegroundColor Yellow
    docker build -f docker\Dockerfile.minimal -t atlas-remote-mcp:v2 .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Build still failing. Try:" -ForegroundColor Red
        Write-Host "  docker system prune -a" -ForegroundColor White
        Write-Host "  Then run this script again" -ForegroundColor White
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "  ✓ Image built successfully" -ForegroundColor Green

# Step 5: Check certificates
if (!(Test-Path "deploy\self-signed\config\certs\server.crt")) {
    Write-Host ""
    Write-Host "[5/5] Generating certificates..." -ForegroundColor Yellow
    Push-Location deploy\self-signed
    if (Test-Path "generate_ssl.ps1") {
        .\generate_ssl.ps1
    } else {
        .\generate_ssl.bat
    }
    Pop-Location
} else {
    Write-Host "[5/5] Certificates already exist" -ForegroundColor Green
}

# Start the server
Write-Host ""
Write-Host "Starting server..." -ForegroundColor Cyan
docker-compose -f docker\docker-compose.https.yml up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  ✅ Rebuild Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Server is starting at: https://localhost:8443" -ForegroundColor Green
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  Check status:  docker ps" -ForegroundColor White
    Write-Host "  View logs:     docker logs atlas-mcp-server" -ForegroundColor White
    Write-Host "  Follow logs:   docker logs -f atlas-mcp-server" -ForegroundColor White
    Write-Host ""
    
    # Wait a moment and check if running
    Start-Sleep -Seconds 3
    $running = docker ps --format "table {{.Names}}" | Select-String "atlas-mcp-server"
    if ($running) {
        Write-Host "✓ Server is running!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Server may still be starting. Check logs if issues persist." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Failed to start server" -ForegroundColor Red
    Write-Host "Check logs: docker logs atlas-mcp-server" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
