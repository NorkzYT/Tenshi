# ==============================================================================
# Makefile for Docker-Based Environment Management
#
# Application: $(APPLICATION_NAME)
# Git Hash: $(GIT_HASH)
#
# This Makefile is organized to provide clear and concise commands for:
# - Running production and development environments.
# - Building (with rebuild) environments.
# - Managing container lifecycle (stop, clean, logs).
#
# Error handling is implemented via dependency checks, and targets are marked
# as .PHONY to ensure they run correctly even if files with the same names exist.
# ==============================================================================

# ---------------------------
# Variable Definitions
# ---------------------------
DOCKER_USERNAME ?= norkz
APPLICATION_NAME ?= tenshi
GIT_HASH ?= $(shell git log --format="%h" -n 1)
COMPOSE_FILE_PROD := docker-compose.yml
COMPOSE_FILE_DEV  := docker-compose.dev.yml

# ---------------------------
# Declare PHONY Targets
# ---------------------------
.PHONY: help check prod dev build-prod build-dev stop clean logs

# ---------------------------
# Dependency Check
# ---------------------------
# This target checks if the required commands are available.
check:
	@command -v docker compose >/dev/null 2>&1 || { \
		echo "Error: docker compose is not installed. Aborting."; exit 1; }
	@command -v docker >/dev/null 2>&1 || { \
		echo "Error: docker is not installed. Aborting."; exit 1; }
	@echo "All required dependencies are installed."

# ---------------------------
# Help Section
# ---------------------------
# Run 'make help' to display available commands.
help:
	@echo "\nAvailable Commands:"
	@echo "--------------------------------------------------------------------------------------"
	@echo "\033[1;35mMain Environment Commands:\033[0m"
	@echo "  \033[1;33mmake prod\033[0m      - Start the production environment using $(COMPOSE_FILE_PROD)."
	@echo "  \033[1;33mmake dev\033[0m       - Start the development environment using $(COMPOSE_FILE_DEV)."
	@echo "  \033[1;33mmake build-prod\033[0m - Build (with rebuild) and run the production environment."
	@echo "  \033[1;33mmake build-dev\033[0m  - Build (with rebuild) and run the development environment."
	@echo "\n\033[1;35mAdditional Commands:\033[0m"
	@echo "  \033[1;33mmake stop\033[0m       - Stop running containers."
	@echo "  \033[1;33mmake clean\033[0m      - Stop and remove containers, networks, images, and volumes."
	@echo "  \033[1;33mmake logs\033[0m       - Follow logs from running containers."
	@echo "  \033[1;33mmake check\033[0m      - Check that all required dependencies are installed."
	@echo "--------------------------------------------------------------------------------------\n"

# ---------------------------
# Production Environment Targets
# ---------------------------
# 'prod' starts the production environment with a force-recreate.
prod: check
	@echo "Starting production environment..."
	docker compose -f $(COMPOSE_FILE_PROD) up -d --force-recreate

# 'build-prod' builds (rebuild) and starts the production environment.
build-prod: check
	@echo "Building production environment..."
	docker compose -f $(COMPOSE_FILE_PROD) up -d --build

# ---------------------------
# Development Environment Targets
# ---------------------------
# 'dev' starts the development environment with a force-recreate.
dev: check
	@echo "Starting development environment..."
	docker compose -f $(COMPOSE_FILE_DEV) up -d --force-recreate

# 'build-dev' builds (rebuild) and starts the development environment.
build-dev: check
	@echo "Building development environment..."
	docker compose -f $(COMPOSE_FILE_DEV) up -d --build

# ---------------------------
# Environment Management Targets
# ---------------------------
# 'stop' stops running containers. It tries the production compose file first,
# then the development one.
stop: check
	@echo "Stopping containers..."
	-docker compose -f $(COMPOSE_FILE_PROD) down || docker compose -f $(COMPOSE_FILE_DEV) down

# 'clean' stops and removes containers, networks, images, and volumes.
clean: check
	@echo "Cleaning environment: stopping and removing all resources..."
	-docker compose -f $(COMPOSE_FILE_PROD) down --rmi all -v --remove-orphans || \
	 docker compose -f $(COMPOSE_FILE_DEV) down --rmi all -v --remove-orphans

# 'logs' follows the logs from running containers.
logs: check
	@echo "Tailing logs from running containers..."
	-docker compose -f $(COMPOSE_FILE_PROD) logs -f || docker compose -f $(COMPOSE_FILE_DEV) logs -f
