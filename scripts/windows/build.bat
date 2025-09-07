@echo off
REM Build Docker image for Atlas Remote MCP

echo ========================================
echo   Building Atlas Remote MCP Docker Image
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to project root (v2) - script is in v2\scripts\windows\
cd /d "%SCRIPT_DIR%\..\.."

REM Show where we are for debugging
echo Building from: %CD%
echo.

REM Clean up old images and containers
echo [1/3] Cleaning up Docker...
docker system prune -f >nul 2>&1
docker rmi atlas-remote-mcp:v2 >nul 2>&1

REM Build with standard Dockerfile
echo [2/3] Building Docker image...
docker build -f deploy\docker\Dockerfile -t atlas-remote-mcp:v2 .
if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Docker image built successfully!
    echo.
    echo To run the server:
    echo   cd deploy\docker
    echo   docker-compose up
    echo.
    echo Or for HTTPS:
    echo   cd deploy\ssl\self-signed-working
    echo   start_https.bat
    echo.
    pause
    exit /b 0
)

REM If that fails, try with minimal requirements
echo.
echo [3/3] Build failed. Trying with minimal requirements...
echo fastmcp>requirements-minimal.txt
echo starlette>>requirements-minimal.txt
echo uvicorn[standard]>>requirements-minimal.txt
echo python-dotenv>>requirements-minimal.txt

REM Backup and replace requirements
copy requirements.txt requirements-backup.txt >nul
copy requirements-minimal.txt requirements.txt >nul

REM Try build again
docker build -f deploy\docker\Dockerfile -t atlas-remote-mcp:v2 .
set build_result=%errorlevel%

REM Restore original requirements
copy requirements-backup.txt requirements.txt >nul
del requirements-backup.txt >nul 2>&1
del requirements-minimal.txt >nul 2>&1

if %build_result% equ 0 (
    echo.
    echo SUCCESS: Docker image built with minimal requirements!
    echo.
    pause
    exit /b 0
) else (
    echo.
    echo ERROR: Build failed. Please check:
    echo   1. Docker Desktop is running
    echo   2. Internet connection is working
    echo   3. Try: docker pull python:3.11-slim
    echo.
    pause
    exit /b 1
)
