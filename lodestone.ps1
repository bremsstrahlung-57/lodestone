$ErrorActionPreference = "Stop"

$InstallDir = "$env:USERPROFILE\.lodestone"
$ConfigDir = "$env:USERPROFILE\.config\lodestone"

$DockerComposeCmd = ""
if (docker compose version 2>$null) {
    $DockerComposeCmd = "docker compose"
} elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $DockerComposeCmd = "docker-compose"
} else {
    Write-Host "Error: Docker Compose is not installed." -ForegroundColor Red
    exit 1
}

function Show-Help {
    Write-Host "Lodestone CLI" -ForegroundColor Cyan
    Write-Host "Usage: lodestone [COMMAND]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start   Start the Lodestone containers"
    Write-Host "  stop    Stop the Lodestone containers"
    Write-Host "  update  Update compose files, CLI tool, pull latest images, and restart"
    Write-Host "  delete  Stop containers and remove Docker images (keeps data/volumes)"
    Write-Host "  prune   Stop containers, remove images, volumes, and installation data (keeps config)"
    Write-Host "  logs    Tail the container logs"
    Write-Host ""
}

$Command = $args[0]

if (-not (Test-Path $InstallDir) -and $Command -ne "help") {
    Write-Host "Lodestone is not installed in $InstallDir." -ForegroundColor Red
    Write-Host "Please run the installation script first."
    exit 1
}

if (Test-Path $InstallDir) {
    Set-Location $InstallDir
}

switch ($Command) {
    "start" {
        Write-Host "Starting Lodestone..." -ForegroundColor Yellow
        if ($DockerComposeCmd -eq "docker compose") { docker compose up -d } else { docker-compose up -d }
        Write-Host "Lodestone started." -ForegroundColor Green
    }
    "stop" {
        Write-Host "Stopping Lodestone..." -ForegroundColor Yellow
        if ($DockerComposeCmd -eq "docker compose") { docker compose down } else { docker-compose down }
        Write-Host "Lodestone stopped." -ForegroundColor Green
    }
    "update" {
        Write-Host "Fetching latest configurations and CLI tool..." -ForegroundColor Yellow
        try {
            Invoke-WebRequest -Uri "https://raw.githubusercontent.com/bremsstrahlung-57/lodestone/master/docker-compose.prod.yml" -OutFile "$InstallDir\docker-compose.yml"
        } catch {
            Write-Host "Warning: Failed to update docker-compose.yml" -ForegroundColor Red
        }

        try {
            Invoke-WebRequest -Uri "https://raw.githubusercontent.com/bremsstrahlung-57/lodestone/master/lodestone.ps1" -OutFile "$env:USERPROFILE\.local\bin\lodestone.ps1"
        } catch {
            Write-Host "Warning: Failed to update CLI tool" -ForegroundColor Red
        }

        Write-Host "Updating Lodestone images..." -ForegroundColor Yellow
        if ($DockerComposeCmd -eq "docker compose") { docker compose pull } else { docker-compose pull }

        Write-Host "Restarting containers with new configurations and images..." -ForegroundColor Yellow
        if ($DockerComposeCmd -eq "docker compose") { docker compose up -d --remove-orphans } else { docker-compose up -d --remove-orphans }

        Write-Host "Update complete!" -ForegroundColor Green
    }
    "delete" {
        Write-Host "Removing Lodestone containers and local images..." -ForegroundColor Yellow
        if ($DockerComposeCmd -eq "docker compose") { docker compose down --rmi local } else { docker-compose down --rmi local }
        Write-Host "Images and containers deleted. (Volumes and configs were kept)" -ForegroundColor Green
    }
    "prune" {
        Write-Host "WARNING: This will completely destroy all Lodestone data and images. (Config will be kept)" -ForegroundColor Red
        $confirmation = Read-Host "Are you sure you want to continue? [y/N]"
        if ($confirmation -match "^[Yy]$") {
            Write-Host "Stopping containers and removing volumes/images..." -ForegroundColor Yellow
            if ($DockerComposeCmd -eq "docker compose") { docker compose down -v --rmi all } else { docker-compose down -v --rmi all }
            Write-Host "Removing installation directory..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
            Remove-Item -Force "$env:USERPROFILE\.local\bin\lodestone.ps1" -ErrorAction SilentlyContinue
            Write-Host "Lodestone has been completely pruned from your system." -ForegroundColor Green
        } else {
            Write-Host "Prune cancelled."
        }
    }
    "logs" {
        if ($DockerComposeCmd -eq "docker compose") { docker compose logs -f } else { docker-compose logs -f }
    }
    default {
        Show-Help
    }
}
