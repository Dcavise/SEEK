# Pre-commit Hooks Setup Guide

This document provides comprehensive instructions for setting up and using pre-commit hooks in the Primer Seek Property Development project.

## Overview

The pre-commit hooks provide automated code quality, security, and formatting checks for both Python (backend) and TypeScript (frontend) code. The configuration ensures consistency across the monorepo structure and prevents common issues from being committed.

## Prerequisites

Before setting up pre-commit hooks, ensure you have the following tools installed:

### System Requirements
- Python 3.12.x
- Node.js 18+ with pnpm 8.x
- Git

### Tool Installation

#### 1. Install pre-commit
```bash
# Using pip
pip install pre-commit

# Or using pipx (recommended)
pipx install pre-commit

# Or using homebrew (macOS)
brew install pre-commit
```

#### 2. Install Python development tools
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies (using Poetry when available)
pip install black ruff mypy bandit safety detect-secrets
```

#### 3. Install Node.js development tools
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
pnpm install

# Or install globally for system-wide availability
npm install -g eslint prettier typescript
```

#### 4. Install additional tools
```bash
# Docker linting
# macOS
brew install hadolint

# Ubuntu/Debian
sudo apt-get install hadolint

# Shell script linting (shellcheck)
# macOS
brew install shellcheck

# Ubuntu/Debian
sudo apt-get install shellcheck
```

## Setup Instructions

### 1. Install pre-commit hooks
```bash
# Navigate to project root
cd /Users/davidcavise/Documents/Windsurf\ Projects/Seek

# Install the git hook scripts
pre-commit install

# Install commit message hook
pre-commit install --hook-type commit-msg
```

### 2. Initialize secrets baseline
```bash
# Create initial secrets baseline
detect-secrets scan --baseline .secrets.baseline

# Update baseline if new secrets are intentionally added
detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins
```

### 3. Test the setup
```bash
# Run all hooks on all files (initial setup)
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run eslint --all-files
```

## Hook Configuration Details

### Python Hooks (Backend)

#### Black - Code Formatting
- **Purpose**: Consistent Python code formatting
- **Configuration**: Line length 88, Python 3.12 target
- **Files**: `backend/**/*.py`

#### Ruff - Linting and Code Quality
- **Purpose**: Fast Python linter with auto-fixes
- **Features**: pycodestyle, pyflakes, isort, bugbear, complexity checks
- **Configuration**: Defined in `backend/pyproject.toml`

#### MyPy - Type Checking
- **Purpose**: Static type checking for Python
- **Configuration**: Strict mode enabled
- **Additional dependencies**: types-requests, types-redis, types-psycopg2

#### Bandit - Security Scanning
- **Purpose**: Security vulnerability detection
- **Configuration**: Excludes test files, generates JSON reports
- **Output**: `bandit-report.json`

#### Safety - Dependency Security
- **Purpose**: Check Python dependencies for known vulnerabilities
- **Target**: `backend/pyproject.toml`

### TypeScript/JavaScript Hooks (Frontend)

#### ESLint - Linting
- **Purpose**: Code quality and consistency for TypeScript/React
- **Configuration**: `frontend/eslint.config.js`
- **Features**: TypeScript strict checks, React hooks validation, import ordering

#### Prettier - Code Formatting
- **Purpose**: Consistent code formatting
- **Configuration**: `frontend/.prettierrc.json`
- **Files**: `.ts`, `.tsx`, `.js`, `.jsx`, `.json`, `.css`, `.scss`, `.md`

#### TypeScript Compiler Check
- **Purpose**: Type checking without emitting files
- **Command**: `npx tsc --noEmit`
- **Target**: `frontend/**/*.{ts,tsx}`

### Security and General Hooks

#### Detect Secrets
- **Purpose**: Prevent secrets from being committed
- **Baseline**: `.secrets.baseline`
- **Excludes**: Lock files, minified files, maps

#### Conventional Commits
- **Purpose**: Enforce conventional commit message format
- **Allowed types**: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
- **Stage**: commit-msg

#### General File Checks
- Trailing whitespace removal
- End-of-file fixing
- Merge conflict detection
- Large file prevention (>500kB)
- YAML/JSON/TOML validation

## Usage

### Normal Development Workflow

Pre-commit hooks run automatically on `git commit`. If any hook fails, the commit is rejected, and you must fix the issues before committing.

```bash
# Make changes to files
git add .

# Commit (hooks run automatically)
git commit -m "feat: add new property search feature"
```

### Manual Hook Execution

```bash
# Run all hooks on staged files
pre-commit run

# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run eslint
pre-commit run mypy

# Run hooks on specific files
pre-commit run --files backend/src/main.py
```

### Bypassing Hooks (Use Sparingly)

```bash
# Skip all hooks (not recommended)
git commit --no-verify -m "emergency fix"

# Skip specific hook
SKIP=black pre-commit run
```

## Troubleshooting

### Common Issues

#### 1. Hook Installation Failures
```bash
# Clear pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit install --install-hooks
```

#### 2. Python Import Errors
```bash
# Ensure Python dependencies are installed
cd backend
pip install -r requirements-dev.txt  # or use Poetry
```

#### 3. Node.js Dependency Issues
```bash
# Reinstall Node.js dependencies
cd frontend
rm -rf node_modules package-lock.json
pnpm install
```

#### 4. TypeScript Compilation Errors
```bash
# Check TypeScript configuration
cd frontend
npx tsc --noEmit --listFiles
```

#### 5. ESLint Configuration Issues
```bash
# Test ESLint configuration
cd frontend
npx eslint --print-config src/App.tsx
```

### Performance Optimization

#### 1. Skip Slow Hooks During Development
```bash
# Skip slow hooks for rapid iteration
SKIP=mypy,eslint git commit -m "wip: working on feature"
```

#### 2. Configure Hook Concurrency
Add to `.pre-commit-config.yaml`:
```yaml
default_install_hook_types: [pre-commit, commit-msg]
default_stages: [commit]
```

## Maintenance

### Updating Hooks
```bash
# Update to latest versions
pre-commit autoupdate

# Update specific repository
pre-commit autoupdate --repo https://github.com/psf/black
```

### Adding New Hooks
1. Edit `.pre-commit-config.yaml`
2. Add new hook configuration
3. Install updated hooks: `pre-commit install`
4. Test: `pre-commit run --all-files`

### Secrets Management
```bash
# Update secrets baseline after adding legitimate secrets
detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins

# Audit detected secrets
detect-secrets audit .secrets.baseline
```

## Integration with IDEs

### VS Code
Install extensions:
- Python (Microsoft)
- ESLint
- Prettier - Code formatter
- GitLens

Configure settings.json:
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

### PyCharm/WebStorm
1. Configure external tools for Black, Ruff, Prettier
2. Set up file watchers for automatic formatting
3. Enable ESLint and TypeScript services

## Continuous Integration

The pre-commit configuration supports pre-commit.ci for automatic maintenance:
- Weekly dependency updates
- Auto-fix PRs for formatting issues
- Consistent checks across local and CI environments

To enable pre-commit.ci:
1. Visit https://pre-commit.ci
2. Install the GitHub app
3. Enable for your repository

## Best Practices

1. **Run hooks locally before pushing**: Avoid CI failures
2. **Fix issues promptly**: Don't accumulate linting debt
3. **Use meaningful commit messages**: Follow conventional commit format
4. **Keep configurations updated**: Regular maintenance prevents issues
5. **Document exceptions**: Use ignore comments sparingly and document why

## Support

For issues with pre-commit hooks:
1. Check this documentation
2. Review hook-specific documentation
3. Check tool-specific configuration files
4. Test individual tools outside pre-commit
5. Consult team for project-specific guidance
