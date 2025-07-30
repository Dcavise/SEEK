# Primer Seek Property - Codebase Documentation

## Project Overview

**Business Context**: The Primer Seek Property sourcing system is a comprehensive platform designed to import, normalize, and visualize property data from all cities in Texas, Alabama, and Florida. The system enables the Primer Real Estate function to efficiently analyze potential property lease opportunities through a high-performance interactive mapping interface.

**Architecture**: Monorepo structure with Python FastAPI backend and React TypeScript frontend, powered by Supabase (PostgreSQL + PostGIS) and DuckDB for high-performance data processing.

**Technology Stack**:
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, asyncpg, Redis
- **Frontend**: React 18, TypeScript 5.x, Vite, Tailwind CSS, Mapbox GL JS, Zustand
- **Database**: Supabase (PostgreSQL + PostGIS), Redis caching, DuckDB for CSV processing
- **Development**: Poetry, pnpm, pre-commit hooks, comprehensive linting/formatting

## Development Instructions

Follow the tasks as outlined in /Users/davidcavise/Documents/Windsurf Projects/Seek/plan.md
If the user wishes to deviate from the plan, confirm that is intentional before proceeding?

When making updates to existing code or scripts, don't create a new file for minor updates, update the existing file.

- Explain the stakes of the question you are asking me when asking for my input or confirmation of an action. Indicate the potential impact.

## Codebase Structure

### Monorepo Organization
```
/Users/davidcavise/Documents/Windsurf Projects/Seek/
├── backend/                    # Python FastAPI application
│   ├── src/
│   │   ├── core/              # Core configuration and infrastructure
│   │   │   ├── config.py      # Application configuration
│   │   │   ├── database.py    # Database connection and session management
│   │   │   ├── exceptions.py  # Custom exception classes
│   │   │   ├── logging.py     # Logging configuration
│   │   │   └── redis.py       # Redis client configuration
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── property.py    # Property data model
│   │   │   └── user.py        # User data model
│   │   ├── schemas/           # Pydantic schemas for API validation
│   │   │   ├── property.py    # Property request/response schemas
│   │   │   └── user.py        # User request/response schemas
│   │   ├── services/          # Business logic layer
│   │   │   └── __init__.py
│   │   └── main.py            # FastAPI application entry point
│   ├── pyproject.toml         # Poetry dependencies and tool configuration
│   └── README.md              # Backend-specific documentation
├── frontend/                  # React TypeScript application
│   ├── src/
│   │   └── App.tsx            # Main React component
│   ├── package.json           # pnpm dependencies and scripts
│   ├── tsconfig.json          # TypeScript configuration
│   ├── tsconfig.node.json     # TypeScript config for build tools
│   └── eslint.config.js       # ESLint configuration
├── shared/                    # Shared types and utilities
│   ├── tsconfig.json          # Shared TypeScript configuration
│   └── README.md
├── scripts/                   # Deployment and utility scripts
│   └── README.md
└── [configuration files]      # Root-level config files
```

### Backend Architecture Pattern
- **Models Layer** (`/models/`): SQLAlchemy ORM models defining database schema
- **Schemas Layer** (`/schemas/`): Pydantic models for API request/response validation
- **Services Layer** (`/services/`): Business logic and data processing
- **Core Layer** (`/core/`): Infrastructure concerns (database, config, logging)
- **FastAPI Application** (`main.py`): Route definitions and app configuration

### Frontend Architecture Pattern
- **Component-based React** with TypeScript for type safety
- **Vite** for fast development and optimized builds
- **ESLint + Prettier** for code quality and formatting
- **Modern React patterns** with hooks and functional components

## Development Workflow

### Environment Setup
1. **Prerequisites**: Python 3.12+, Node.js 18+, Poetry 2.1+, pnpm 8.15+
2. **Environment Management**: Uses `direnv` with `.envrc` for automatic environment variable loading
3. **Package Management**: Poetry for Python dependencies, pnpm for Node.js dependencies

### Pre-commit Hooks (Comprehensive Quality Checks)
**Automatically runs on every commit**:
- **Python Quality**:
  - `ruff` - Fast Python linter with extensive rule set
  - `black` - Code formatting with 88-character line length
  - `mypy` - Static type checking with strict configuration
  - `bandit` - Security vulnerability scanning
- **TypeScript Quality**:
  - `ESLint` - Linting with TypeScript, React, and import rules
  - `Prettier` - Code formatting for consistent style
  - `TypeScript compiler` - Type checking and compilation verification
- **General Quality**:
  - Trailing whitespace removal, file ending fixes
  - YAML/JSON/TOML syntax validation
  - Merge conflict detection, large file prevention
  - Secret detection with `detect-secrets`
  - Conventional commit message validation

### Code Quality Standards
- **Type Safety**: Strict TypeScript and mypy configurations enforced
- **Security**: Bandit scanning, secret detection, dependency vulnerability checks
- **Consistency**: Automated formatting with Black and Prettier
- **Import Organization**: Sorted imports with proper grouping
- **Test Coverage**: pytest with coverage reporting for backend

### Git Workflow
- **Pre-commit hooks** ensure code quality before commits
- **Conventional commits** for clear commit history
- **Branch protection** with quality checks in CI/CD

## API & Data Models

### Current FastAPI Endpoints
**Base URL**: `http://localhost:8000`

- **GET /** - Root endpoint returning API information
- **GET /health** - Health check endpoint for monitoring

### Data Model Architecture

#### SQLAlchemy Models (`/backend/src/models/`)
- **Property Model** (`property.py`): Core property data with geospatial information
- **User Model** (`user.py`): User authentication and profile data
- **Database Integration**: PostgreSQL with PostGIS for geospatial queries

#### Pydantic Schemas (`/backend/src/schemas/`)
- **Property Schemas** (`property.py`): Request/response validation for property endpoints
- **User Schemas** (`user.py`): User registration, authentication, and profile schemas
- **Validation**: Comprehensive input validation with Pydantic v2

#### Database Strategy
- **Primary Database**: Supabase (PostgreSQL + PostGIS) for production data
- **Caching Layer**: Redis for high-performance data access
- **Analytics Database**: DuckDB for high-speed CSV processing and analytics
- **Connection Management**: SQLAlchemy 2.0 with async support

### Planned API Endpoints (from plan.md)
- **Property Management**: CRUD operations for property data
- **Geospatial Queries**: Location-based property searches
- **Data Import**: Bulk CSV import from TX/AL/FL sources
- **User Authentication**: JWT-based authentication system
- **Analytics**: Property market analysis and reporting

## Development Commands & Scripts

### Backend Commands (Poetry)
```bash
# Navigate to backend directory
cd backend/

# Development server (FastAPI with auto-reload)
poetry run dev
# Alternative: poetry run python -m src.main

# Install dependencies
poetry install

# Add new dependencies
poetry add package-name
poetry add --group dev package-name  # For dev dependencies

# Run tests
poetry run pytest
poetry run pytest --cov=src  # With coverage

# Code quality checks
poetry run black src/  # Format code
poetry run ruff check src/  # Lint code
poetry run ruff check --fix src/  # Auto-fix issues
poetry run mypy src/  # Type checking

# Database operations (planned)
poetry run alembic upgrade head  # Run migrations
poetry run alembic revision --autogenerate -m "description"  # Create migration
```

### Frontend Commands (pnpm)
```bash
# Navigate to frontend directory
cd frontend/

# Development server (Vite with HMR)
pnpm dev

# Install dependencies
pnpm install

# Add new dependencies
pnpm add package-name
pnpm add -D package-name  # For dev dependencies

# Build for production
pnpm build

# Code quality checks
pnpm lint  # ESLint
pnpm lint:fix  # ESLint with auto-fix
pnpm format  # Prettier formatting
pnpm format:check  # Check formatting
pnpm type-check  # TypeScript compilation check

# Preview production build
pnpm preview
```

### Pre-commit Commands
```bash
# Install pre-commit hooks (run once)
pre-commit install --hook-type pre-commit --hook-type commit-msg

# Run hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run eslint --all-files

# Update hook versions
pre-commit autoupdate
```

### Environment Management (direnv)
```bash
# Allow environment loading (run once in project root)
direnv allow

# Reload environment
direnv reload

# Check environment status
direnv status
```

## Architecture Decisions & Patterns

### Technology Choices & Rationale

#### Backend Architecture
- **FastAPI**: Chosen for automatic OpenAPI documentation, async support, and excellent TypeScript client generation
- **SQLAlchemy 2.0**: Modern ORM with async support, type safety, and excellent PostgreSQL integration
- **Pydantic v2**: Fast serialization/validation with automatic OpenAPI schema generation
- **Poetry**: Superior dependency management with lock files and virtual environment handling
- **Async/Await Pattern**: Enables high-performance I/O operations for database and external API calls

#### Database Strategy
- **PostgreSQL + PostGIS**: Industry standard for geospatial applications, required for TX/AL/FL property data
- **Supabase**: Provides PostgreSQL with real-time subscriptions, authentication, and admin interface
- **Redis**: High-performance caching for frequently accessed property data and user sessions
- **DuckDB**: Column-oriented database optimized for analytical queries on large CSV datasets

#### Frontend Architecture
- **React 18**: Component-based architecture with modern hooks and concurrent features
- **TypeScript 5.x**: Type safety, better developer experience, and compile-time error detection
- **Vite**: Fast development server with HMR and optimized production builds
- **Tailwind CSS**: Utility-first CSS framework for consistent design system
- **Mapbox GL JS**: High-performance mapping for property visualization

### Security Patterns
- **Environment Variables**: Sensitive configuration stored in `.env` files, never committed
- **Secret Detection**: Pre-commit hooks scan for accidentally committed secrets
- **Dependency Scanning**: Bandit for Python security issues, dependency vulnerability checks
- **Type Safety**: Strict TypeScript and mypy configurations prevent runtime errors
- **Input Validation**: Pydantic schemas validate all API inputs

### Performance Considerations
- **Async Database Operations**: Non-blocking I/O for better concurrency
- **Connection Pooling**: SQLAlchemy manages database connection pools
- **Redis Caching**: Frequently accessed data cached for sub-millisecond response times
- **Geospatial Indexing**: PostGIS spatial indexes for fast location-based queries
- **Frontend Optimization**: Vite's tree-shaking and code splitting for minimal bundle sizes

### Code Organization Principles
- **Separation of Concerns**: Models, schemas, services, and routes in separate modules
- **Dependency Injection**: FastAPI's dependency system for testability and modularity
- **Type-First Development**: Pydantic models define API contracts and database schemas
- **Test-Driven Patterns**: Comprehensive test coverage with pytest and React Testing Library
- **Documentation as Code**: OpenAPI specs auto-generated from Pydantic models
