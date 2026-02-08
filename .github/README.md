# GitHub Configuration

This directory contains GitHub-specific configuration files for the OmniContent project.

## 📁 Contents

### Workflows (`.github/workflows/`)

Automated CI/CD pipelines that run on push and pull request events:

#### 1. **Backend CI** (`backend-ci.yml`)

**Triggers**: Push/PR to `main` or `develop` with backend changes

**Jobs**:
- **Test**: Runs on Python 3.11
  - Installs dependencies
  - Runs database migrations
  - Executes test suite
  - Tests API endpoints
- **Lint**: Code quality checks
  - Ruff (linting)
  - Black (formatting)
  - isort (import sorting)
  - mypy (type checking)
- **Security**: Security scanning
  - Bandit (security issues)
  - Safety (dependency vulnerabilities)

**Status**: Tests continue on error for visibility

#### 2. **Frontend CI** (`frontend-ci.yml`)

**Triggers**: Push/PR to `main` or `develop` with frontend changes

**Jobs**:
- **Lint and Build**: Code quality and build verification
  - ESLint checking
  - TypeScript type checking
  - Build process
  - Build size reporting
- **Test**: Unit tests (when implemented)

#### 3. **PR Checks** (`pr-checks.yml`)

**Triggers**: PR opened, synchronized, or reopened

**Jobs**:
- **PR Metadata**:
  - Validates PR title (conventional commits format)
  - Checks PR size (<1000 lines recommended)
  - Verifies Co-authored-by tag for AI assistance
- **Files Changed**:
  - Reports which parts of codebase changed
  - Updates GitHub summary
- **Code Review Checklist**:
  - Posts review checklist on new PRs

#### 4. **Database Migration Check** (`database-migration-check.yml`)

**Triggers**: PR with changes to migrations or models

**Jobs**:
- **Migration Check**:
  - Tests migration can run
  - Verifies reversibility (downgrade/upgrade)
  - Checks for migration conflicts
  - Validates naming conventions
  - Scans for dangerous operations (DROP)
  - Generates migration summary

### Templates

#### Pull Request Template (`PULL_REQUEST_TEMPLATE.md`)

Comprehensive template that includes:
- Change description
- Type of change checklist
- Database changes section
- Testing instructions
- Code quality checklist
- Security checklist
- Documentation checklist
- Deployment notes
- Performance impact
- Backward compatibility

**Usage**: Automatically loads when creating a PR

#### Code Owners (`CODEOWNERS`)

Defines code ownership for automatic review requests:
- Backend code: @ZhengZhenyu
- Frontend code: @ZhengZhenyu
- Documentation: @ZhengZhenyu
- Configuration: @ZhengZhenyu

**Usage**: Automatically requests reviews from owners

## 🚀 Using the CI/CD Pipeline

### For Contributors

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes** following coding standards

3. **Commit with conventional commits**:
   ```bash
   git commit -m "feat(api): add new endpoint"
   ```

4. **Push and create PR**:
   ```bash
   git push -u origin feature/your-feature
   ```

5. **Wait for CI checks** to complete
   - All checks should be green ✅
   - Fix any failing checks

6. **Request review** from code owners

### Viewing CI Results

#### In Pull Requests

- **Checks tab**: See all workflow runs
- **Files changed**: View inline annotations from linters
- **Conversation**: See automated comments

#### In Actions Tab

- Navigate to repository → Actions
- Click on a workflow run to see details
- Download artifacts (security reports, coverage)

### Common CI Failures

#### Backend CI

**Linting Errors**:
```bash
# Fix locally
cd backend
black app/
isort app/
ruff check app/ --fix
```

**Test Failures**:
```bash
# Run tests locally
cd backend
pytest -v
```

**Migration Issues**:
```bash
# Test migration
alembic upgrade head
alembic downgrade -1
```

#### Frontend CI

**Build Failures**:
```bash
# Fix locally
cd frontend
npm run build
```

**Lint Errors**:
```bash
# Fix locally
npm run lint --fix
```

## 🔧 Workflow Configuration

### Modifying Workflows

1. Edit workflow files in `.github/workflows/`
2. Test changes in a feature branch
3. Verify workflows run correctly
4. Merge to main

### Adding New Checks

Example: Adding coverage requirements

```yaml
# In backend-ci.yml, add:
- name: Check coverage threshold
  run: |
    pytest --cov=app --cov-fail-under=80
```

### Skipping CI

To skip CI on a commit (use sparingly):

```bash
git commit -m "docs: update README [skip ci]"
```

## 📊 Status Badges

Add to main README.md:

```markdown
![Backend CI](https://github.com/ZhengZhenyu/omnicontent/workflows/Backend%20CI/badge.svg)
![Frontend CI](https://github.com/ZhengZhenyu/omnicontent/workflows/Frontend%20CI/badge.svg)
![PR Checks](https://github.com/ZhengZhenyu/omnicontent/workflows/PR%20Checks/badge.svg)
```

## 🔐 Secrets and Variables

### Required Secrets

Currently no secrets required for CI.

Future additions might include:
- `CODECOV_TOKEN` - For coverage reporting
- `SLACK_WEBHOOK` - For notifications
- `DEPLOY_KEY` - For deployment

### Setting Secrets

1. Go to repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add name and value
4. Use in workflows: `${{ secrets.SECRET_NAME }}`

## 📈 Monitoring

### Workflow Run History

- View all runs: Repository → Actions
- Filter by workflow, branch, or status
- Download logs for debugging

### Notifications

GitHub sends notifications for:
- Workflow failures on your branches
- PR check failures
- Review requests (from CODEOWNERS)

Configure in: Settings → Notifications

## 🛠️ Troubleshooting

### Workflow Not Triggering

**Check**:
1. File path filters match changed files
2. Branch name matches trigger conditions
3. Workflow file syntax is valid

**Solution**:
```bash
# Validate workflow syntax
npx @action-validator/core validate .github/workflows/backend-ci.yml
```

### Permission Errors

**Issue**: `Resource not accessible by integration`

**Solution**: Check workflow permissions in repository settings

### Cache Issues

**Clear npm cache**:
```yaml
- name: Clear cache
  run: npm cache clean --force
```

**Clear pip cache**: Delete cache manually in Actions → Caches

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Contributing Guide](../docs/CONTRIBUTING.md)

---

💡 **Tip**: Enable "Required status checks" in branch protection to enforce CI before merging.
