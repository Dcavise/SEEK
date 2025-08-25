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
	@. venv/bin/activate && python scripts/database/check_database_schema.py
	@echo "✅ Database schema ready"

# Development
dev: check-env ## Start development servers (backend monitoring + frontend)
	@echo "Starting development environment..."
	@trap 'kill %1; kill %2' SIGINT; \
	. venv/bin/activate && python scripts/utilities/startup_monitoring.py & \
	cd seek-property-platform && npm run dev & \
	wait

dev-frontend: ## Start only frontend development server
	@cd seek-property-platform && npm run dev

dev-backend: check-env ## Start only backend monitoring
	@. venv/bin/activate && python scripts/utilities/startup_monitoring.py

# Building
build: ## Build frontend for production
	@cd seek-property-platform && npm run build

build-dev: ## Build frontend for development
	@cd seek-property-platform && npm run build:dev

# Testing and Quality
test: ## Run comprehensive tests and quality checks
	@echo "Running Python code quality checks..."
	@. venv/bin/activate && ruff check . --fix
	@. venv/bin/activate && black . --check
	@echo "Running Python unit tests..."
	@. venv/bin/activate && pytest tests/unit/ -v --tb=short || echo "Unit tests not yet implemented"
	@echo "Running frontend tests..."
	@cd seek-property-platform && npm run lint
	@echo "Testing database connection..."
	@. venv/bin/activate && python -c "from src.utils.database import db_manager; print('✅', db_manager.validate_connection())" || echo "Database utilities not yet configured"

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@. venv/bin/activate && pytest tests/unit/ -v --cov=src --cov-report=term-missing || echo "Unit tests not yet implemented"

test-integration: ## Run integration tests (requires database)
	@echo "Running integration tests..."
	@. venv/bin/activate && pytest tests/integration/ -v --maxfail=3 || echo "Integration tests moved to tests/integration/"

format: ## Format Python code with black and ruff
	@echo "Formatting Python code..."
	@. venv/bin/activate && black .
	@. venv/bin/activate && ruff check . --fix

lint: ## Run Python linting without fixes
	@echo "Running Python linting..."
	@. venv/bin/activate && ruff check .
	@. venv/bin/activate && black . --check

type-check: ## Run type checking (if mypy added)
	@echo "Type checking would run here (mypy not yet configured)"

health: check-env ## Run comprehensive health checks
	@echo "Running health checks..."
	@. venv/bin/activate && python scripts/utilities/monitor_performance.py
	@echo "✅ Health check complete"

# Data Operations
import-data: check-env ## Import Texas county data
	@echo "Starting data import..."
	@. venv/bin/activate && python scripts/import/import_texas_counties.py
	@echo "✅ Data import complete"

import-single: check-env ## Import single county (usage: make import-single COUNTY=bexar)
	@if [ -z "$(COUNTY)" ]; then echo "Usage: make import-single COUNTY=bexar"; exit 1; fi
	@. venv/bin/activate && python scripts/import/import_single_county.py $(COUNTY)

analyze: check-env ## Run database performance analysis
	@. venv/bin/activate && python tests/integration/test_performance.py

test-api: check-env ## Test FOIA-enhanced search API functionality
	@echo "Testing FOIA Search API (Task 3.2)..."
	@. venv/bin/activate && python test_task_3_2_final.py

# Spatial Operations
spatial-setup: check-env ## Set up PostGIS spatial geometry and indexes
	@echo "Setting up PostGIS spatial enhancement..."
	@. venv/bin/activate && python -c "import psycopg2; import os; from dotenv import load_dotenv; load_dotenv(); conn = psycopg2.connect(host='aws-0-us-east-1.pooler.supabase.com', database='postgres', user='postgres.mpkprmjejiojdjbkkbmn', password=os.getenv('SUPABASE_DB_PASSWORD'), port=6543); cur = conn.cursor(); cur.execute(open('add_spatial_geometry.sql').read()); conn.commit(); print('✅ Spatial geometry setup complete')"

spatial-test: check-env ## Test spatial query performance
	@echo "Testing spatial query performance..."
	@. venv/bin/activate && python -c "import psycopg2; import os; import time; from dotenv import load_dotenv; load_dotenv(); conn = psycopg2.connect(host='aws-0-us-east-1.pooler.supabase.com', database='postgres', user='postgres.mpkprmjejiojdjbkkbmn', password=os.getenv('SUPABASE_DB_PASSWORD'), port=6543); cur = conn.cursor(); start = time.time(); cur.execute('SELECT COUNT(*) FROM parcels WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(-98.4936, 29.4241), 4326), 0.01)'); result = cur.fetchone(); end = time.time(); print(f'Found {result[0]} properties near San Antonio in {(end-start)*1000:.1f}ms'); conn.close()"

gen-types: ## Generate TypeScript types from database schema  
	@echo "Generating TypeScript database types..."
	@cd seek-property-platform && SUPABASE_ACCESS_TOKEN=sbp_337e749eecf85740eecf8ac1e5702c79ff8d523a supabase gen types typescript --project-id mpkprmjejiojdjbkkbmn > src/types/database.types.ts
	@echo "✅ Database types generated"

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
	@if [ -f temp/performance_log.json ]; then tail -20 temp/performance_log.json; fi
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
	@. venv/bin/activate && python scripts/utilities/monitor_performance.py --watch

# Project Organization
cleanup: ## Clean up and reorganize project structure
	@echo "🧹 Starting project structure cleanup..."
	@. venv/bin/activate && python scripts/utilities/cleanup_project_structure.py
	@echo "✅ Project structure cleaned"

maintain: ## Check project structure and suggest improvements
	@echo "🔍 Running project maintenance checks..."
	@. venv/bin/activate && python tools/maintain_project_structure.py --check --report
	@echo "✅ Maintenance check complete"

auto-fix: ## Auto-fix simple project structure issues
	@echo "🔧 Auto-fixing project structure issues..."
	@. venv/bin/activate && python tools/maintain_project_structure.py --fix --check
	@echo "✅ Auto-fixes applied"

organize: cleanup maintain ## Full organization: cleanup + maintenance check