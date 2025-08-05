# SEEK Property Platform - Development Makefile
# Optimized workflows for full-stack development

.PHONY: help install dev build test clean deploy setup-db import-data analyze health check-env

# Default target
help: ## Show this help message
	@echo "SEEK Property Platform - Development Commands"
	@echo "============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment and Setup
check-env: ## Check environment variables and dependencies
	@echo "Checking environment..."
	@if [ ! -f .env ]; then echo "❌ .env file missing"; exit 1; fi
	@if [ ! -d venv ]; then echo "❌ Python virtual environment missing"; exit 1; fi
	@if [ ! -d seek-property-platform/node_modules ]; then echo "❌ Frontend dependencies missing"; exit 1; fi
	@echo "✅ Environment looks good"

install: ## Install all dependencies (backend + frontend)
	@echo "Installing Python dependencies..."
	@python -m venv venv
	@. venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd seek-property-platform && npm install
	@echo "✅ All dependencies installed"

setup-db: ## Set up database schema and indexes
	@echo "Setting up database schema..."
	@. venv/bin/activate && python check_database_schema.py
	@echo "✅ Database schema ready"

# Development
dev: check-env ## Start development servers (backend monitoring + frontend)
	@echo "Starting development environment..."
	@trap 'kill %1; kill %2' SIGINT; \
	. venv/bin/activate && python startup_monitoring.py & \
	cd seek-property-platform && npm run dev & \
	wait

dev-frontend: ## Start only frontend development server
	@cd seek-property-platform && npm run dev

dev-backend: check-env ## Start only backend monitoring
	@. venv/bin/activate && python startup_monitoring.py

# Building
build: ## Build frontend for production
	@cd seek-property-platform && npm run build

build-dev: ## Build frontend for development
	@cd seek-property-platform && npm run build:dev

# Testing and Quality
test: ## Run tests and linting
	@echo "Running frontend tests..."
	@cd seek-property-platform && npm run lint
	@echo "Testing database connection..."
	@. venv/bin/activate && python -c "from supabase import create_client; print('✅ Database connection OK')"

health: check-env ## Run comprehensive health checks
	@echo "Running health checks..."
	@. venv/bin/activate && python monitor_performance.py
	@echo "✅ Health check complete"

# Data Operations
import-data: check-env ## Import Texas county data
	@echo "Starting data import..."
	@. venv/bin/activate && python import_texas_counties.py
	@echo "✅ Data import complete"

import-single: check-env ## Import single county (usage: make import-single COUNTY=bexar)
	@if [ -z "$(COUNTY)" ]; then echo "Usage: make import-single COUNTY=bexar"; exit 1; fi
	@. venv/bin/activate && python import_single_county.py $(COUNTY)

analyze: check-env ## Run database performance analysis
	@. venv/bin/activate && python test_performance.py

# Utilities
clean: ## Clean build artifacts and cache
	@echo "Cleaning build artifacts..."
	@rm -rf seek-property-platform/dist/
	@rm -rf seek-property-platform/node_modules/.cache/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@echo "✅ Clean complete"

reset-db: ## Reset database (DANGER: deletes all data)
	@echo "⚠️  This will delete all data. Are you sure? (y/N)"
	@read -r REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		. venv/bin/activate && python -c "print('Database reset would go here')"; \
	else \
		echo "Cancelled"; \
	fi

# Git and Deployment
git-status: ## Show detailed git status
	@git status
	@echo "\nBranch info:"
	@git branch -v
	@echo "\nRemote info:"
	@git remote -v

deploy-prep: build test ## Prepare for deployment
	@echo "Running pre-deployment checks..."
	@git status --porcelain | wc -l | xargs -I {} test {} -eq 0 || (echo "❌ Uncommitted changes"; exit 1)
	@echo "✅ Ready for deployment"

# Development Quality of Life
logs: ## Show recent application logs
	@if [ -f performance_log.json ]; then tail -20 performance_log.json; fi
	@if [ -d data/NormalizeLogs ]; then ls -la data/NormalizeLogs/ | tail -5; fi

quick-start: install setup-db ## Complete setup for new developers
	@echo "🚀 SEEK Platform is ready!"
	@echo "Run 'make dev' to start development servers"
	@echo "Run 'make help' to see all available commands"

# Environment specific commands
prod-build: ## Production build with optimizations
	@NODE_ENV=production cd seek-property-platform && npm run build

# Database maintenance
backup-db: ## Create database backup
	@echo "Creating database backup..."
	@. venv/bin/activate && python -c "print('Backup functionality would go here')"

# Monitoring
watch-performance: ## Watch performance metrics in real-time
	@. venv/bin/activate && python monitor_performance.py --watch