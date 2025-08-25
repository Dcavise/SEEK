#!/bin/bash
# Install SEEK Property Platform Git Hooks

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔗 Setting up Git hooks for SEEK Property Platform..."

# Install pre-commit hook
if [ -f "$PROJECT_ROOT/tools/pre-commit-hook" ]; then
    cp "$PROJECT_ROOT/tools/pre-commit-hook" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit" 
    echo "✅ Pre-commit hook installed"
else
    echo "❌ Pre-commit hook source not found"
    exit 1
fi

# Create a simple pre-push hook to run tests
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# SEEK Property Platform Pre-push Hook

echo "🧪 Pre-push: Running quick tests..."

# Run linting and basic checks
make lint > /dev/null 2>&1 || (echo "❌ Linting failed"; exit 1)

# Check that frontend builds
cd seek-property-platform && npm run build > /dev/null 2>&1 || (echo "❌ Frontend build failed"; exit 1)

echo "✅ Pre-push checks passed"
EOF

chmod +x "$HOOKS_DIR/pre-push"
echo "✅ Pre-push hook installed"

echo ""
echo "Git hooks installed successfully!"
echo ""
echo "The hooks will:"
echo "  • Pre-commit: Check project structure and prevent clutter"
echo "  • Pre-push: Run linting and build checks"
echo ""
echo "To bypass hooks temporarily: git commit --no-verify"
echo "To test hooks manually: .git/hooks/pre-commit"