$ErrorActionPreference = "Stop"

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "      Installing Lodestone...          " -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# 1. Prerequisite Checks
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed." -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://docs.docker.com/desktop/install/windows-install/ and try again."
    exit 1
}

$DockerComposeCmd = ""
if (docker compose version 2>$null) {
    $DockerComposeCmd = "docker compose"
} elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $DockerComposeCmd = "docker-compose"
} else {
    Write-Host "Error: Docker Compose is not installed." -ForegroundColor Red
    Write-Host "Please install Docker Compose and try again."
    exit 1
}

# 2. Define Installation Directories
$InstallDir = "$env:USERPROFILE\.lodestone"
$ConfigDir = "$env:USERPROFILE\.config\lodestone"
$DataDir = "$InstallDir\data"

Write-Host "Setting up directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

# 3. Download docker-compose.prod.yml
$ComposeUrl = "https://raw.githubusercontent.com/bremsstrahlung-57/lodestone/master/docker-compose.prod.yml"
$ComposeFile = "$InstallDir\docker-compose.yml"

Write-Host "Downloading production docker-compose file..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $ComposeUrl -OutFile $ComposeFile
} catch {
    Write-Host "Failed to download docker-compose.yml. Please check your internet connection or the repository URL." -ForegroundColor Red
    exit 1
}

# 4. Start the Application
Write-Host "Pulling latest Docker images and starting Lodestone..." -ForegroundColor Yellow
Set-Location $InstallDir

if ($DockerComposeCmd -eq "docker compose") {
    docker compose pull
    docker compose up -d
} else {
    docker-compose pull
    docker-compose up -d
}

# 5. Install the CLI Wrapper
$BinDir = "$env:USERPROFILE\.local\bin"
$CliUrl = "https://raw.githubusercontent.com/bremsstrahlung-57/lodestone/master/lodestone.ps1"
$CliFile = "$BinDir\lodestone.ps1"

Write-Host "Installing lodestone CLI tool..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

try {
    Invoke-WebRequest -Uri $CliUrl -OutFile $CliFile

    # Check if ~/.local/bin is in PATH for CurrentUser
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($UserPath -notmatch [regex]::Escape($BinDir)) {
        Write-Host "Adding $BinDir to your User PATH..." -ForegroundColor Yellow
        $NewPath = $UserPath + ";$BinDir"
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        $env:Path = $env:Path + ";$BinDir"
    }
} catch {
    Write-Host "Failed to download lodestone CLI tool. You can still use docker compose commands manually." -ForegroundColor Red
}

# 6. Post-Installation Summary
Write-Host ""
Write-Host "🚀 Lodestone installed and started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Web Interface (Frontend): http://localhost:8090" -ForegroundColor Cyan
Write-Host "⚙️  API Endpoint (Backend):   http://localhost:8091/api" -ForegroundColor Cyan
Write-Host "🗄️  Vector DB (Qdrant):       http://localhost:8092/dashboard" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Data is stored in:     $InstallDir" -ForegroundColor Yellow
Write-Host "📁 Config is stored in:   $ConfigDir" -ForegroundColor Yellow
Write-Host ""
Write-Host "To view logs, run:      lodestone logs" -ForegroundColor Yellow
Write-Host "To stop Lodestone, run: lodestone stop" -ForegroundColor Yellow
Write-Host "=======================================" -ForegroundColor Cyan
