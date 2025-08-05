#!/bin/bash
# SEEK Property Platform - Developer Setup Script
# Automated setup for new team members

set -e

echo "🏠 SEEK Property Platform - Developer Setup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "CLAUDE.md" ]; then
    echo "❌ Please run this script from the SEEK project root directory"
    exit 1
fi

# Check for required tools
echo "Checking required tools..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed"  
    exit 1
fi

echo "✅ Required tools found"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "Please create .env file with your Supabase credentials:"
    echo "SUPABASE_URL=your_supabase_url"
    echo "SUPABASE_ANON_KEY=your_supabase_anon_key"
    echo "SUPABASE_SERVICE_ROLE_KEY=your_service_role_key"
    exit 1
fi

echo "✅ Environment file found"

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed"

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd seek-property-platform
npm install
cd ..
echo "✅ Frontend dependencies installed"

# Test database connection
echo "Testing database connection..."
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')

if not url or not key:
    print('❌ Missing Supabase credentials in .env file')
    exit(1)

try:
    supabase = create_client(url, key)
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Run 'make dev' to start development servers"
echo "2. Run 'make help' to see all available commands"
echo "3. Visit http://localhost:5173 to see the frontend"
echo ""
echo "Useful commands:"
echo "- make dev          # Start both backend and frontend"
echo "- make import-data  # Import Texas county data"
echo "- make test         # Run tests and linting"
echo "- make health       # Check system health"