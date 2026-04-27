#!/usr/bin/env bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}      Installing Lodestone...          ${NC}"
echo -e "${BLUE}=======================================${NC}"

# 1. Prerequisite Checks
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker from https://docs.docker.com/get-started/get-docker/ and try again."
    exit 1
fi

DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    echo "Please install Docker Compose and try again."
    exit 1
fi

# 2. Define Installation Directories
INSTALL_DIR="$HOME/.lodestone"
CONFIG_DIR="$HOME/.config/lodestone"
DATA_DIR="$INSTALL_DIR/data"

echo -e "${YELLOW}Setting up directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"

# 3. Download docker-compose.prod.yml
COMPOSE_URL="https://raw.githubusercontent.com/bremsstrahlung-57/lodestone/master/docker-compose.prod.yml"
COMPOSE_FILE="$INSTALL_DIR/docker-compose.yml"

echo -e "${YELLOW}Downloading production docker-compose file...${NC}"
if ! curl -sSLf "$COMPOSE_URL" -o "$COMPOSE_FILE"; then
    echo -e "${RED}Failed to download docker-compose.yml. Please check your internet connection or the repository URL.${NC}"
    exit 1
fi

# 4. Start the Application
echo -e "${YELLOW}Pulling latest Docker images and starting Lodestone...${NC}"
cd "$INSTALL_DIR"

$DOCKER_COMPOSE_CMD pull

$DOCKER_COMPOSE_CMD up -d

# 5. Install the CLI Wrapper
BIN_DIR="$HOME/.local/bin"
CLI_URL="https://raw.githubusercontent.com/bremsstrahlung-57/lodestone/master/lodestone"
CLI_FILE="$BIN_DIR/lodestone"

echo -e "${YELLOW}Installing lodestone CLI tool...${NC}"
mkdir -p "$BIN_DIR"
if curl -sSLf "$CLI_URL" -o "$CLI_FILE"; then
    chmod +x "$CLI_FILE"
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo -e "${YELLOW}Note: $BIN_DIR is not in your PATH.${NC}"
        echo -e "You might want to add 'export PATH=\"\$HOME/.local/bin:\$PATH\"' to your ~/.bashrc or ~/.zshrc."
    fi
else
    echo -e "${RED}Failed to download lodestone CLI tool. You can still use docker compose commands manually.${NC}"
fi

# 6. Post-Installation Summary
echo -e ""
echo -e "${GREEN}🚀 Lodestone installed and started successfully!${NC}"
echo -e ""
echo -e "🌐 ${BLUE}Web Interface (Frontend):${NC} http://localhost:8090"
echo -e "⚙️  ${BLUE}API Endpoint (Backend):${NC}   http://localhost:8091/api"
echo -e "🗄️  ${BLUE}Vector DB (Qdrant):${NC}       http://localhost:8092/dashboard"
echo -e ""
echo -e "📁 ${YELLOW}Data is stored in:${NC}     $INSTALL_DIR"
echo -e "📁 ${YELLOW}Config is stored in:${NC}   $CONFIG_DIR"
echo -e ""
echo -e "To view logs, run:      ${YELLOW}lodestone logs${NC}"
echo -e "To stop Lodestone, run: ${YELLOW}lodestone stop${NC}"
echo -e "${BLUE}=======================================${NC}"
