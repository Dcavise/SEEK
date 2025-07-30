#!/bin/bash

# Switch Environment Script for Primer Seek
# Usage: ./scripts/switch-env.sh [main|develop]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

show_usage() {
    echo "Usage: $0 [main|develop]"
    echo ""
    echo "Switch between main and develop branch environments:"
    echo "  main     - Use production Supabase project (fnysbvwgefnligvfsuhs)"
    echo "  develop  - Use develop branch project (goowadpoiciscdcxpwtm) with microschool compliance system"
    echo ""
    echo "Examples:"
    echo "  $0 develop    # Switch to develop branch with compliance testing data"
    echo "  $0 main       # Switch to main branch production database"
}

switch_to_main() {
    echo "🔄 Switching to MAIN branch environment..."

    # Backup current .env if it exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.env.backup"
        echo "   Backed up current .env to .env.backup"
    fi

    # Copy main environment config
    if [ -f "$PROJECT_ROOT/.env.main" ]; then
        cp "$PROJECT_ROOT/.env.main" "$PROJECT_ROOT/.env"
        echo "   ✅ Using main branch configuration (.env.main)"
    else
        echo "   ⚠️  .env.main not found, using default production settings"
        cat > "$PROJECT_ROOT/.env" << 'EOF'
# Main Branch Environment - Production Database
ENVIRONMENT=production
SUPABASE_URL=https://fnysbvwgefnligvfsuhs.supabase.co
export DATABASE_URL=postgresql://postgres:Logistimatics123%21@db.fnysbvwgefnligvfsuhs.supabase.co:5432/postgres
EOF
    fi

    echo "   🎯 Main branch active:"
    echo "       Database: fnysbvwgefnligvfsuhs.supabase.co"
    echo "       Features: Basic properties and users tables"
    echo ""
}

switch_to_develop() {
    echo "🔄 Switching to DEVELOP branch environment..."

    # Backup current .env if it exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.env.backup"
        echo "   Backed up current .env to .env.backup"
    fi

    # Copy develop environment config
    if [ -f "$PROJECT_ROOT/.env.develop" ]; then
        cp "$PROJECT_ROOT/.env.develop" "$PROJECT_ROOT/.env"
        echo "   ✅ Using develop branch configuration (.env.develop)"
    else
        echo "   ❌ .env.develop not found! Please ensure develop branch is properly configured."
        exit 1
    fi

    echo "   🎯 Develop branch active:"
    echo "       Database: goowadpoiciscdcxpwtm.supabase.co"
    echo "       Features: Full microschool compliance system"
    echo "                - FOIA data integration"
    echo "                - Tier classification (Tier 1/2/3/Disqualified)"
    echo "                - Property owner intelligence"
    echo "                - Compliance scoring and history"
    echo "                - PostGIS geospatial operations"
    echo "                - Test data seeded and ready"
    echo ""
}

show_current_env() {
    echo "🔍 Current Environment Status:"

    if [ -f "$PROJECT_ROOT/.env" ]; then
        # Extract key info from .env
        SUPABASE_URL=$(grep "^SUPABASE_URL=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2 || echo "Not set")
        export # Declare and assign separately
        DATABASE_URL_TEMP=$(grep "^DATABASE_URL=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2 || echo "Not set")
        export DATABASE_URL="$DATABASE_URL_TEMP"

        echo "   Supabase URL: $SUPABASE_URL"

        if [[ "$SUPABASE_URL" == *"goowadpoiciscdcxpwtm"* ]]; then
            echo "   🟢 DEVELOP branch active (with microschool compliance system)"
        elif [[ "$SUPABASE_URL" == *"fnysbvwgefnligvfsuhs"* ]]; then
            echo "   🔵 MAIN branch active (production database)"
        else
            echo "   ⚠️  Unknown environment configuration"
        fi
    else
        echo "   ❌ No .env file found"
    fi
    echo ""
}

# Main script logic
case "${1:-}" in
    "main")
        switch_to_main
        ;;
    "develop")
        switch_to_develop
        ;;
    "status"|"")
        show_current_env
        show_usage
        ;;
    *)
        echo "❌ Invalid option: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac

# Show final status
show_current_env

echo "🚀 Environment switch complete!"
echo "   Next steps:"
echo "   1. Restart your backend server: cd backend && poetry run dev"
echo "   2. Restart your frontend: cd frontend && pnpm dev"
echo "   3. Test database connection and compliance features"
