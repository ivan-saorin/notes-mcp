@echo off
REM ==================================================
REM   Windows Quick Setup - Remote MCP Server v2
REM   Self-Signed Certificate Method
REM ==================================================

echo.
echo ============================================
echo   Remote MCP Server v2 - Windows Setup
echo ============================================
echo.
echo This script will:
echo   1. Check prerequisites
echo   2. Generate SSL certificates
echo   3. Build Docker image
echo   4. Start the HTTPS server
echo   5. Show configuration instructions
echo.
pause

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to project root (v2) - script is in v2\scripts\windows\
cd /d "%SCRIPT_DIR%\..\.."

echo Working from: %CD%
echo.

REM Check Docker
echo [1/5] Checking Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Docker Desktop is not running!
    echo.
    echo Please:
    echo   1. Install Docker Desktop from https://docker.com
    echo   2. Start Docker Desktop
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)
echo Docker Desktop is running [OK]

REM Check certificates
echo.
echo [2/5] Checking certificates...
if not exist "deploy\ssl\self-signed-working\certs\server.crt" (
    echo Generating new certificates...
    cd deploy\ssl\self-signed-working
    call generate_ssl.bat
    cd /d "%SCRIPT_DIR%\..\.."
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Certificate generation failed
        echo Try using PowerShell instead:
        echo   cd deploy\ssl\self-signed-working
        echo   .\generate_ssl.ps1
        pause
        exit /b 1
    )
) else (
    echo Certificates already exist [OK]
)

REM Build Docker image
echo.
echo [3/5] Building Docker image...
docker build -f deploy\docker\Dockerfile -t atlas-remote-mcp:v2 . >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker build failed, trying with verbose output...
    docker build -f deploy\docker\Dockerfile -t atlas-remote-mcp:v2 .
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Docker build failed
        echo Try running: scripts\windows\build.bat
        pause
        exit /b 1
    )
)
echo Docker image built [OK]

REM Start the server
echo.
echo [4/5] Starting HTTPS server...
cd deploy\ssl\self-signed-working
call start_https.bat
cd /d "%SCRIPT_DIR%\..\.."
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Server failed to start
    pause
    exit /b 1
)

REM Show configuration
echo.
echo [5/5] Configuration Instructions
echo ============================================
echo.
echo Your MCP server is now running at:
echo   https://localhost:8443/mcp
echo.
echo To configure Claude Desktop:
echo.
echo 1. Open this file in Notepad:
echo    %%APPDATA%%\Claude\claude_desktop_config.json
echo.
echo 2. Add this configuration:
echo    {
echo      "mcpServers": {
echo        "atlas-remote": {
echo          "url": "https://localhost:8443/mcp",
echo          "transport": "streamable-http"
echo        }
echo      }
echo    }
echo.
echo 3. Save the file and restart Claude Desktop
echo.
echo 4. Test by asking Claude:
echo    "Use the remote MCP server to calculate 100 + 200"
echo.
echo ============================================
echo.
pause
