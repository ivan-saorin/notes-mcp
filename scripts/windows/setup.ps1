# Windows Quick Setup Script for Remote MCP Server v2
# PowerShell all-in-one setup with self-signed certificates

param(
    [switch]$SkipCertificates,
    [switch]$AutoTrust
)

# Set window title
$host.UI.RawUI.WindowTitle = "Remote MCP Server v2 - Windows Setup"

# Pretty banner
function Show-Banner {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  Remote MCP Server v2 - Windows Setup" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This script will:" -ForegroundColor White
    Write-Host "  1. Check prerequisites" -ForegroundColor Gray
    Write-Host "  2. Generate SSL certificates" -ForegroundColor Gray
    Write-Host "  3. Build and start the HTTPS server" -ForegroundColor Gray
    Write-Host "  4. Configure Claude Desktop" -ForegroundColor Gray
    Write-Host ""
}

# Check if running as admin
function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal] $identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
}

# Main setup function
function Start-Setup {
    Show-Banner
    
    # Check admin privileges
    if ($AutoTrust -and !(Test-Administrator)) {
        Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
        Write-Host "Certificate won't be auto-trusted. Run as admin for auto-trust." -ForegroundColor Yellow
        Write-Host ""
        $continue = Read-Host "Continue anyway? (Y/N)"
        if ($continue -ne 'Y' -and $continue -ne 'y') {
            exit
        }
    }
    
    Write-Host "Starting setup..." -ForegroundColor Green
    Write-Host ""
    
    # Step 1: Check Docker
    Write-Host "[1/5] Checking Docker Desktop..." -ForegroundColor Cyan
    try {
        docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker not responding"
        }
        Write-Host "  ✓ Docker Desktop is running" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Docker Desktop is not running!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please:" -ForegroundColor Yellow
        Write-Host "  1. Install Docker Desktop from https://docker.com" -ForegroundColor White
        Write-Host "  2. Start Docker Desktop" -ForegroundColor White
        Write-Host "  3. Run this script again" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Step 2: Generate certificates
    if (!$SkipCertificates) {
        Write-Host ""
        Write-Host "[2/5] Setting up certificates..." -ForegroundColor Cyan
        
        $certPath = "deploy\self-signed\config\certs\server.crt"
        if (Test-Path $certPath) {
            Write-Host "  ✓ Certificates already exist" -ForegroundColor Green
            $regen = Read-Host "  Regenerate certificates? (Y/N)"
            if ($regen -eq 'Y' -or $regen -eq 'y') {
                & "deploy\self-signed\generate_ssl.ps1"
            }
        } else {
            Write-Host "  Generating new certificates..." -ForegroundColor Yellow
            & "deploy\self-signed\generate_ssl.ps1"
        }
    }
    
    # Step 3: Build Docker image
    Write-Host ""
    Write-Host "[3/5] Building Docker image..." -ForegroundColor Cyan
    Write-Host "  This may take a few minutes on first run..." -ForegroundColor Gray
    
    # Build with output to see any errors
    $buildResult = docker build -f docker\Dockerfile -t atlas-remote-mcp:v2 . 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Docker image built successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to build Docker image" -ForegroundColor Red
        Write-Host ""
        Write-Host "Build output:" -ForegroundColor Yellow
        Write-Host $buildResult
        Write-Host ""
        Write-Host "Common fixes:" -ForegroundColor Cyan
        Write-Host "  1. Ensure Docker Desktop is running" -ForegroundColor White
        Write-Host "  2. Try: docker system prune -a" -ForegroundColor White
        Write-Host "  3. Check internet connection" -ForegroundColor White
        exit 1
    }
    
    # Step 4: Start server
    Write-Host ""
    Write-Host "[4/5] Starting HTTPS server..." -ForegroundColor Cyan
    
    # Stop any existing containers
    docker-compose -f docker\docker-compose.https.yml down 2>&1 | Out-Null
    
    # Start the server
    docker-compose -f docker\docker-compose.https.yml up -d 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Server started successfully" -ForegroundColor Green
        
        # Wait for server to be ready
        Start-Sleep -Seconds 3
        
        # Test the endpoint
        try {
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
            $response = Invoke-WebRequest -Uri "https://localhost:8443/" -UseBasicParsing -TimeoutSec 5
            Write-Host "  ✓ Server is responding on https://localhost:8443" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ Server started but certificate warning is normal" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ Failed to start server" -ForegroundColor Red
        docker logs atlas-mcp-server
        exit 1
    }
    
    # Step 5: Configure Claude Desktop
    Write-Host ""
    Write-Host "[5/5] Claude Desktop Configuration" -ForegroundColor Cyan
    
    $configPath = "$env:APPDATA\claude\claude_desktop_config.json"
    $configDir = "$env:APPDATA\claude"
    
    # Create directory if it doesn't exist
    if (!(Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    # Check if config exists
    if (Test-Path $configPath) {
        Write-Host "  ⚠ Config file already exists" -ForegroundColor Yellow
        Write-Host "  Location: $configPath" -ForegroundColor Gray
        $edit = Read-Host "  Open in notepad to edit? (Y/N)"
        if ($edit -eq 'Y' -or $edit -eq 'y') {
            notepad $configPath
        }
    } else {
        # Create new config
        $config = @{
            mcpServers = @{
                "remote-mcp" = @{
                    url = "https://localhost:8443/mcp/sse"
                }
            }
        }
        $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
        Write-Host "  ✓ Created Claude Desktop config" -ForegroundColor Green
        Write-Host "  Location: $configPath" -ForegroundColor Gray
    }
    
    # Success!
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  ✅ Setup Complete!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Server Status:" -ForegroundColor Cyan
    Write-Host "  HTTPS Endpoint: " -NoNewline
    Write-Host "https://localhost:8443" -ForegroundColor Green
    Write-Host "  MCP Endpoint:   " -NoNewline
    Write-Host "https://localhost:8443/mcp/sse" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Restart Claude Desktop (quit from system tray)" -ForegroundColor White
    Write-Host "  2. Open Claude Desktop" -ForegroundColor White
    Write-Host "  3. Test with: 'Use the remote MCP server to calculate 42 * 17'" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful Commands:" -ForegroundColor Cyan
    Write-Host "  View logs:  " -NoNewline
    Write-Host "docker logs -f atlas-mcp-server" -ForegroundColor Gray
    Write-Host "  Stop:       " -NoNewline
    Write-Host "docker-compose -f docker\docker-compose.https.yml down" -ForegroundColor Gray
    Write-Host "  Restart:    " -NoNewline
    Write-Host "docker-compose -f docker\docker-compose.https.yml restart" -ForegroundColor Gray
    Write-Host ""
    
    # Offer to test
    $test = Read-Host "Open https://localhost:8443 in browser to test? (Y/N)"
    if ($test -eq 'Y' -or $test -eq 'y') {
        Start-Process "https://localhost:8443"
    }
}

# Run the setup
try {
    Start-Setup
} catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Stack Trace:" -ForegroundColor Gray
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
}

Write-Host ""
Read-Host "Press Enter to exit"
