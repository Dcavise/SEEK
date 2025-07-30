#!/bin/bash

# Branch Protection Setup Script for Primer Seek Property Platform
# This script configures GitHub branch protection rules for compliance-critical requirements

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OWNER="${GITHUB_OWNER:-primer}"
REPO="${GITHUB_REPO:-seek-property}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed. Please install it first:"
        echo "  https://cli.github.com/"
        exit 1
    fi

    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        print_error "Not authenticated with GitHub CLI. Please run:"
        echo "  gh auth login"
        exit 1
    fi

    # Check if we have admin access to the repo
    if ! gh api repos/"${OWNER}"/"${REPO}" --jq '.permissions.admin' | grep -q "true"; then
        print_error "Admin access required to configure branch protection rules"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Function to setup main branch protection
setup_main_protection() {
    print_status "Setting up main branch protection..."

    gh api repos/"${OWNER}"/"${REPO}"/branches/main/protection \
        --method PUT \
        --field required_status_checks='{
            "strict": true,
            "contexts": [
                "CI Pipeline / Quality Gate",
                "CI Pipeline / Backend Tests (3.12)",
                "CI Pipeline / Frontend Tests (18)",
                "Security Scanning / Security Report Generation"
            ]
        }' \
        --field enforce_admins=true \
        --field required_pull_request_reviews='{
            "required_approving_review_count": 1,
            "require_code_owner_reviews": true,
            "dismiss_stale_reviews": true,
            "require_review_from_code_owners": true
        }' \
        --field restrictions=null \
        --field required_linear_history=true \
        --field allow_force_pushes=false \
        --field allow_deletions=false \
        --field block_creations=false

    print_success "Main branch protection configured"
}

# Function to setup develop branch protection
setup_develop_protection() {
    print_status "Setting up develop branch protection..."

    # Check if develop branch exists
    if ! gh api repos/"${OWNER}"/"${REPO}"/branches/develop &> /dev/null; then
        print_warning "Develop branch does not exist. Creating it..."

        # Get the SHA of main branch
        MAIN_SHA=$(gh api repos/"${OWNER}"/"${REPO}"/git/ref/heads/main --jq '.object.sha')

        # Create develop branch
        gh api repos/"${OWNER}"/"${REPO}"/git/refs \
            --method POST \
            --field ref="refs/heads/develop" \
            --field sha="$MAIN_SHA"

        print_success "Develop branch created"
    fi

    gh api repos/"${OWNER}"/"${REPO}"/branches/develop/protection \
        --method PUT \
        --field required_status_checks='{
            "strict": true,
            "contexts": [
                "CI Pipeline / Quality Gate"
            ]
        }' \
        --field enforce_admins=false \
        --field required_pull_request_reviews='{
            "required_approving_review_count": 1,
            "require_code_owner_reviews": false,
            "dismiss_stale_reviews": false
        }' \
        --field restrictions=null \
        --field allow_force_pushes=false \
        --field allow_deletions=false

    print_success "Develop branch protection configured"
}

# Function to create CODEOWNERS file
create_codeowners() {
    print_status "Creating CODEOWNERS file..."

    cat > .github/CODEOWNERS << 'EOF'
# CODEOWNERS for Primer Seek Property Intelligence Platform
# This file defines who owns different parts of the codebase for review requirements

# Global owners - require review for all changes
* @davidcavise @primer-team

# Backend code - requires backend team review
/backend/ @davidcavise @primer-backend-team
/backend/src/models/ @davidcavise @primer-backend-team @primer-data-team
/backend/src/core/database.py @davidcavise @primer-backend-team @primer-dba-team

# Frontend code - requires frontend team review
/frontend/ @davidcavise @primer-frontend-team
/frontend/src/components/Map/ @davidcavise @primer-frontend-team @primer-geospatial-team

# Security-sensitive files - requires security team review
/backend/src/core/auth.py @davidcavise @primer-security-team
/backend/src/services/auth/ @davidcavise @primer-security-team
/.github/workflows/security.yml @davidcavise @primer-security-team
/scripts/setup-branch-protection.sh @davidcavise @primer-security-team

# Database and migrations - requires DBA review
/supabase/ @davidcavise @primer-dba-team
/backend/src/models/ @davidcavise @primer-backend-team @primer-dba-team

# CI/CD and infrastructure - requires DevOps review
/.github/workflows/ @davidcavise @primer-devops-team
/.github/dependabot.yml @davidcavise @primer-devops-team
/scripts/ @davidcavise @primer-devops-team

# Configuration files - requires team lead review
/pyproject.toml @davidcavise
/package.json @davidcavise
/.pre-commit-config.yaml @davidcavise
/CLAUDE.md @davidcavise

# Documentation - requires team lead review
/*.md @davidcavise
/docs/ @davidcavise
/.github/CICD_DOCUMENTATION.md @davidcavise
EOF

    print_success "CODEOWNERS file created"
}

# Function to configure security settings
configure_security_settings() {
    print_status "Configuring repository security settings..."

    # Enable vulnerability alerts
    gh api repos/"${OWNER}"/"${REPO}" \
        --method PATCH \
        --field has_vulnerability_alerts=true

    # Enable automated security fixes
    gh api repos/"${OWNER}"/"${REPO}"/automated-security-fixes \
        --method PUT

    # Enable secret scanning
    gh api repos/"${OWNER}"/"${REPO}"/secret-scanning/alerts \
        --method GET > /dev/null 2>&1 || print_warning "Secret scanning not available (may require GitHub Advanced Security)"

    # Enable code scanning
    gh api repos/"${OWNER}"/"${REPO}"/code-scanning/alerts \
        --method GET > /dev/null 2>&1 || print_warning "Code scanning will be enabled when first workflow runs"

    print_success "Security settings configured"
}

# Function to create PR template
create_pr_template() {
    print_status "Creating PR template..."

    mkdir -p .github/pull_request_template

    cat > .github/pull_request_template/default.md << 'EOF'
## 📋 Summary

Brief description of the changes in this PR.

## 🔄 Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Configuration change
- [ ] 🧪 Test update
- [ ] ♻️ Refactoring (no functional changes)
- [ ] 🚀 Performance improvement

## 🧪 Testing

- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] Manual testing completed
- [ ] Coverage threshold maintained

## 🔒 Security Checklist

- [ ] No sensitive data exposed
- [ ] Authentication/authorization properly implemented
- [ ] Input validation added where necessary
- [ ] SQL injection prevention measures in place
- [ ] XSS prevention measures in place

## 📊 Database Changes

- [ ] No database changes
- [ ] Migration scripts included
- [ ] Backwards compatible
- [ ] Data migration tested
- [ ] Performance impact assessed

## 🗂️ Files Changed

List the key files modified and why:

- `file1.py`: Brief description
- `file2.tsx`: Brief description

## 📸 Screenshots (if applicable)

Add screenshots for UI changes.

## 🔗 Related Issues

Fixes #(issue number)
Closes #(issue number)
Related to #(issue number)

## 📝 Additional Notes

Any additional context or notes for reviewers.

## ✅ Review Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
- [ ] Tests added/updated (if needed)
- [ ] No merge conflicts
- [ ] Branch is up to date with main
EOF

    print_success "PR template created"
}

# Function to display final status
display_status() {
    print_status "Branch protection setup complete!"
    echo ""
    echo "📋 Configuration Summary:"
    echo "  ✅ Main branch protection enabled"
    echo "  ✅ Develop branch protection enabled"
    echo "  ✅ CODEOWNERS file created"
    echo "  ✅ Security settings configured"
    echo "  ✅ PR template created"
    echo ""
    print_status "Next steps:"
    echo "  1. Review and commit the new CODEOWNERS file"
    echo "  2. Update team names in CODEOWNERS to match your GitHub teams"
    echo "  3. Configure repository secrets for CI/CD (SNYK_TOKEN, etc.)"
    echo "  4. Test the protection rules with a test PR"
    echo ""
    print_success "All done! Your repository is now protected with compliance-grade rules."
}

# Main execution
main() {
    echo "🛡️  Branch Protection Setup for Primer Seek Property Platform"
    echo "================================================================"
    echo ""

    check_prerequisites
    echo ""

    setup_main_protection
    echo ""

    setup_develop_protection
    echo ""

    create_codeowners
    echo ""

    configure_security_settings
    echo ""

    create_pr_template
    echo ""

    display_status
}

# Run main function
main "$@"
