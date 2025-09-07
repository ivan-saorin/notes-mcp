@echo off
REM Install dependencies for local testing

echo ========================================
echo   Installing MCP Server Dependencies
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to project root (v2) - script is in v2\scripts\windows\
cd /d "%SCRIPT_DIR%\..\.."

echo Installing from: %CD%
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo Installing required packages...
echo.

REM Upgrade pip first
echo [1/3] Upgrading pip...
python -m pip install --upgrade pip

REM Install from requirements.txt
echo.
echo [2/3] Installing requirements...
pip install -r requirements.txt

REM Verify key packages
echo.
echo [3/3] Verifying installation...
python -c "import fastmcp; print('FastMCP installed successfully')"
if %errorlevel% neq 0 (
    echo WARNING: FastMCP not installed, trying alternative...
    pip install fastmcp
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo You can now test locally with:
echo   cd tests
echo   python test_local.py
echo.
echo Or run the server directly:
echo   python run_server.py
echo.
echo For Docker build:
echo   scripts\windows\build.bat
echo.
pause
