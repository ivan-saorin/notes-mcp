@echo off
REM Run the remote MCP server directly

echo ========================================
echo   Atlas Remote MCP Server v2.0.0
echo ========================================
echo.
echo Transport: streamable-http
echo Endpoint: http://localhost:8000/mcp
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to project root (v2) - script is in v2\scripts\windows\
cd /d "%SCRIPT_DIR%\..\.."

echo Starting server from: %CD%
echo.

python run_server.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Server failed to start
    echo Check that all dependencies are installed:
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)
