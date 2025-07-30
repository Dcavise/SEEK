# GitHub Actions CI/CD Pipeline
## Primer Seek Property Intelligence Platform

This directory contains the comprehensive CI/CD pipeline configuration for the Primer Seek property intelligence platform, designed for compliance-critical microschool data handling.

## 📁 Directory Structure

```
.github/
├── workflows/              # GitHub Actions workflows
│   ├── ci.yml             # Main CI pipeline
│   ├── security.yml       # Security scanning
│   ├── pr-labeler.yml     # Automatic PR labeling
│   └── cleanup.yml        # Artifact/cache cleanup
├── ISSUE_TEMPLATE/        # Issue templates
│   └── security.yml       # Security vulnerability reports
├── dependabot.yml         # Dependency update automation
├── labeler.yml           # PR labeling configuration
├── CICD_DOCUMENTATION.md  # Comprehensive pipeline docs
└── README.md             # This file
```

## 🔄 Workflow Overview

### Core Pipelines

#### 1. CI Pipeline (`ci.yml`)
**Triggers**: Push to main/develop, Pull Requests
**Duration**: ~8-10 minutes
**Features**:
- ✅ Parallel backend/frontend testing
- ✅ Change detection optimization
- ✅ Comprehensive code quality checks
- ✅ Coverage reporting (90% backend, 85% frontend)
- ✅ Integration with Supabase + Redis

#### 2. Security Pipeline (`security.yml`)
**Triggers**: Push, PRs, Weekly schedule
**Duration**: ~5-7 minutes
**Features**:
- ✅ Dependency vulnerability scanning
- ✅ SAST with CodeQL, Bandit, Semgrep
- ✅ Secret detection with TruffleHog
- ✅ Container security with Trivy
- ✅ Zero-tolerance compliance reporting

#### 3. Dependency Management (`dependabot.yml`)
**Schedule**: Weekly updates
**Features**:
- ✅ Automated security patches
- ✅ Grouped dependency updates
- ✅ Poetry + pnpm support
- ✅ GitHub Actions updates

## 🎯 Quality Gates

### Branch Protection Requirements

#### Main Branch
- ✅ All CI checks must pass
- ✅ Security scan approval required
- ✅ 1+ code owner review
- ✅ Up-to-date branch required
- ✅ No HIGH/CRITICAL vulnerabilities

#### Coverage Thresholds
- **Backend**: 90% minimum (compliance requirement)
- **Frontend**: 85% target
- **Security**: Zero tolerance for HIGH/CRITICAL

## 🚀 Quick Start

### 1. Enable Workflows
All workflows are ready to use. Simply push to trigger the CI pipeline.

### 2. Configure Branch Protection
```bash
# Apply recommended branch protection rules
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["CI Pipeline / Quality Gate"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"require_code_owner_reviews":true}'
```

### 3. Required Secrets
Add these secrets to your GitHub repository:

```yaml
Repository Secrets:
  SNYK_TOKEN: "your-snyk-token"           # For vulnerability scanning
  SEMGREP_APP_TOKEN: "your-semgrep-token" # For SAST analysis
  CODECOV_TOKEN: "your-codecov-token"     # For coverage reporting
```

### 4. Configure Notifications
Set up team notifications in repository settings:
- **Security alerts**: Enable for all team members
- **Dependabot**: Configure security update notifications
- **Action failures**: Set up Slack/email notifications

## 📊 Monitoring & Reporting

### Automated Reports
- **PR Comments**: Detailed CI/security results
- **Security Tab**: SARIF uploads for vulnerabilities
- **Coverage Reports**: Codecov integration
- **Artifact Storage**: 30-day retention for reports

### Performance Metrics
- **CI Runtime**: Target < 10 minutes
- **Cache Hit Rate**: Monitored for optimization
- **Security Scan Coverage**: 100% codebase coverage
- **Dependency Updates**: Weekly automated reviews

## 🔧 Customization

### Adding New Workflows
1. Create workflow file in `.github/workflows/`
2. Follow naming convention: `feature-name.yml`
3. Include proper error handling and notifications
4. Update this README with workflow description

### Modifying Quality Gates
1. Update thresholds in workflow environment variables
2. Modify branch protection rules accordingly
3. Document changes in `CICD_DOCUMENTATION.md`
4. Communicate changes to development team

### Security Configuration
1. Review `.github/workflows/security.yml`
2. Update vulnerability thresholds as needed
3. Modify secret detection patterns
4. Configure compliance reporting requirements

## 🚨 Troubleshooting

### Common Issues

#### CI Pipeline Failures
```bash
# Check workflow run logs
gh run list --limit 5
gh run view <run-id> --log

# Common fixes
- Clear cache: Delete and re-run
- Check service dependencies: PostgreSQL/Redis health
- Verify environment variables: Check secret configuration
```

#### Security Scan Failures
```bash
# Review security findings
gh api repos/:owner/:repo/code-scanning/alerts

# Common fixes
- Update .secrets.baseline for false positives
- Review Bandit configuration in pyproject.toml
- Update dependency versions for vulnerabilities
```

#### Cache Issues
```bash
# Clear repository caches
gh api repos/:owner/:repo/actions/caches --method DELETE

# Verify cache keys in workflow logs
# Check cache hit rates in Actions tab
```

## 📞 Support

### Contact Information
- **CI/CD Issues**: Development Team
- **Security Concerns**: Security Team (`security@primer.com`)
- **Emergency**: Critical pipeline failures

### Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Comprehensive CI/CD Documentation](.github/CICD_DOCUMENTATION.md)
- [Security Vulnerability Reporting](.github/ISSUE_TEMPLATE/security.yml)

## 🔄 Updates & Maintenance

### Regular Tasks
- **Weekly**: Review Dependabot PRs
- **Monthly**: Update workflow versions
- **Quarterly**: Security audit and compliance review

### Version Updates
When updating workflow dependencies:
1. Test in feature branch first
2. Update documentation
3. Communicate changes to team
4. Monitor for 48 hours post-deployment

---

**Last Updated**: $(date)
**Pipeline Version**: v1.0.0
**Compliance Status**: ✅ Ready for Production
