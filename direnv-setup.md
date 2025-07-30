# Development Environment Setup with direnv

This project uses [direnv](https://direnv.net/) to automatically manage environment variables and development tools when you enter the project directory.

## Quick Start

1. **Install direnv** (if not already installed):
   ```bash
   # macOS with Homebrew
   brew install direnv

   # Ubuntu/Debian
   sudo apt install direnv

   # Other systems: see https://direnv.net/docs/installation.html
   ```

2. **Hook direnv into your shell** (add to your shell config):
   ```bash
   # For bash: add to ~/.bashrc
   eval "$(direnv hook bash)"

   # For zsh: add to ~/.zshrc
   eval "$(direnv hook zsh)"

   # For fish: add to ~/.config/fish/config.fish
   direnv hook fish | source
   ```

3. **Allow the .envrc file** (first time only):
   ```bash
   cd /path/to/primer-seek-property
   direnv allow
   ```

4. **Create your environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

## What's Included

The `.envrc` file automatically sets up:

- **Python Environment**: Python 3.12.x with Poetry support
- **Node.js Environment**: Node.js 20.x with pnpm 8.x
- **Database Configuration**: Supabase PostgreSQL with PostGIS
- **Caching**: Redis configuration
- **External Services**: Mapbox, authentication, etc.
- **Development Tools**: Helpful aliases and PATH configuration

## Available Aliases

Once direnv is active, you have access to these shortcuts:

### Backend Development
- `backend-dev` - Start FastAPI development server
- `backend-test` - Run Python tests
- `backend-shell` - Enter Poetry virtual environment
- `backend-install` - Install Python dependencies

### Frontend Development
- `frontend-dev` - Start React development server
- `frontend-build` - Build for production
- `frontend-test` - Run frontend tests
- `frontend-install` - Install Node.js dependencies

### Database Management
- `db-migrate` - Run database migrations
- `db-reset` - Reset database to clean state
- `db-shell` - Open PostgreSQL shell

### Project Management
- `setup-all` - Install all dependencies (backend + frontend)
- `test-all` - Run all tests
- `lint-all` - Run all linters
- `format-all` - Format all code

## Environment Variables

All required environment variables are documented in `.env.example`. Key categories include:

- **Database**: Supabase URL, keys, connection strings
- **Authentication**: JWT secrets, session configuration
- **External Services**: Mapbox token, third-party APIs
- **Development**: Debug settings, logging, performance monitoring

## First-Time Setup

1. **Set up Supabase**:
   - Create a new Supabase project
   - Copy URL and keys to your `.env` file
   - Enable PostGIS extension

2. **Configure Mapbox**:
   - Get a Mapbox access token
   - Add to your `.env` file

3. **Set up Redis**:
   - Use local Redis or cloud service
   - Update connection URL in `.env`

4. **Generate Secrets**:
   - Create strong JWT and session secrets
   - Use tools like `openssl rand -hex 32`

## Troubleshooting

### direnv not loading
- Ensure direnv is hooked into your shell
- Run `direnv reload` to force reload
- Check `direnv allow` has been run

### Missing environment variables
- Copy `.env.example` to `.env`
- Fill in all required values
- Check for typos in variable names

### Tool not found errors
- Ensure Python 3.12.x is installed
- Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Install pnpm: `npm install -g pnpm@8`

### Database connection issues
- Verify Supabase project is active
- Check database URL and credentials
- Ensure PostGIS extension is enabled

## Manual Setup (Alternative)

If you prefer not to use direnv, you can manually:

1. Export environment variables from `.env`
2. Install Python dependencies: `cd backend && poetry install`
3. Install Node.js dependencies: `cd frontend && pnpm install`
4. Set up database connection and run migrations

## Security Notes

- **Never commit** `.env` files to version control
- **Rotate secrets** regularly in production
- **Use different** secrets for each environment
- **Limit access** to service role keys
- **Monitor usage** of API keys and tokens

---

For more details, see the project documentation and [plan.md](./plan.md).
