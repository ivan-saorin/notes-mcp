@echo off
REM Quick rebuild script to fix current issues

echo ========================================
echo   Quick Fix and Rebuild
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to project root (v2) - script is in v2\scripts\windows\
cd /d "%SCRIPT_DIR%\..\.."

echo Rebuilding from: %CD%
echo.

REM Stop all containers
echo [1/5] Stopping containers...
docker-compose -f deploy\docker\docker-compose.https.yml down 2>nul
docker-compose -f deploy\docker\docker-compose.yml down 2>nul
docker stop atlas-mcp-https 2>nul
docker rm atlas-mcp-https 2>nul

REM Remove old images to force rebuild
echo [2/5] Removing old images...
docker rmi atlas-remote-mcp:v2 2>nul

REM Clear Docker build cache
echo [3/5] Clearing Docker cache...
docker builder prune -f 2>nul

REM Rebuild with main Dockerfile
echo [4/5] Building fresh image...
docker build --no-cache -f deploy\docker\Dockerfile -t atlas-remote-mcp:v2 .
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed
    echo Try: docker system prune -a
    pause
    exit /b 1
)

REM Start the server
echo [5/5] Starting server...
cd deploy\ssl\self-signed-working
if not exist "certs\server.crt" (
    echo.
    echo Generating certificates first...
    call generate_ssl.bat
)
cd /d "%SCRIPT_DIR%\..\.."
docker-compose -f deploy\docker\docker-compose.https.yml up -d

echo.
echo ========================================
echo   Rebuild Complete!
echo ========================================
echo.
echo Check status with: docker ps
echo View logs with: docker logs atlas-mcp-server
echo.
pause
