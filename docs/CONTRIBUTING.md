# Contributing to OmniContent

Thank you for considering contributing to OmniContent! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)

## Code of Conduct

This project follows a professional and respectful code of conduct. Please be kind and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/ZhengZhenyu/omnicontent.git
cd omnicontent

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# Frontend setup
cd ../frontend
npm install

# Run development servers
# Backend: uvicorn app.main:app --reload
# Frontend: npm run dev
```

## Development Workflow

### Branching Strategy

We use a feature branch workflow:

- `main` - Production-ready code
- `develop` - Integration branch (optional)
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring

### Creating a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature"

# Push to remote
git push -u origin feature/your-feature-name
```

## Coding Standards

### Backend (Python)

We use the following tools to maintain code quality:

- **Black** - Code formatting (line length: 120)
- **Ruff** - Fast linting
- **isort** - Import sorting
- **mypy** - Type checking (optional)

Run formatters before committing:

```bash
cd backend

# Format code
black app/

# Sort imports
isort app/

# Check linting
ruff check app/
```

### Code Style Guidelines

- Use type hints where possible
- Keep functions small and focused (single responsibility)
- Write descriptive variable and function names
- Add docstrings for public functions/classes
- Use f-strings for string formatting
- Avoid deeply nested code (max 3 levels)

### Example

```python
from typing import Optional
from sqlalchemy.orm import Session
from app.models import User


async def get_user_by_email(
    email: str,
    db: Session,
) -> Optional[User]:
    """
    Retrieve a user by their email address.

    Args:
        email: The user's email address
        db: Database session

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `build`: Build system changes
- `ci`: CI/CD changes

### Examples

```bash
# Simple feature
git commit -m "feat: add user authentication"

# With scope
git commit -m "feat(auth): implement JWT token refresh"

# With body
git commit -m "fix(api): resolve content filtering bug

The content API was not properly filtering by community_id,
causing users to see content from other communities.

Closes #123"

# Breaking change
git commit -m "feat(api)!: redesign authentication API

BREAKING CHANGE: Authentication endpoints moved from /auth to /api/auth"
```

### AI-Assisted Development

If you use AI tools (Claude, GitHub Copilot, etc.), add a co-author tag:

```bash
git commit -m "feat: implement calendar view

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## Pull Request Process

### Before Creating a PR

1. **Update your branch** with the latest main:
   ```bash
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run tests** and ensure they pass:
   ```bash
   cd backend
   pytest
   ```

3. **Format code**:
   ```bash
   black app/
   isort app/
   ```

4. **Check linting**:
   ```bash
   ruff check app/
   ```

### Creating the PR

1. Push your branch to GitHub
2. Create a Pull Request using the PR template
3. Fill out all sections of the template
4. Link related issues
5. Request review from code owners

### PR Title

Follow conventional commits format:

```
feat(auth): add OAuth2 integration
fix(api): resolve pagination bug
docs: update API documentation
```

### PR Size Guidelines

- **Small** (<100 lines): Quick review, merge within 1 day
- **Medium** (100-500 lines): Normal review process
- **Large** (500-1000 lines): May need to be split
- **Very Large** (>1000 lines): Should be split into multiple PRs

If your PR is >1000 lines, consider:
- Breaking into smaller, logical PRs
- Creating a feature branch and multiple PRs into it
- Providing extra documentation

### Review Process

1. **Automated Checks**: CI/CD must pass
2. **Code Review**: At least one approval required
3. **Testing**: Manual testing if needed
4. **Documentation**: Ensure docs are updated
5. **Merge**: Squash and merge preferred

## Testing Guidelines

### Backend Tests

Create tests in `backend/tests/`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_user_login():
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Test Coverage

- Aim for >80% code coverage
- Test happy paths and error cases
- Test authentication and authorization
- Test database operations

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_user_login

# Run in verbose mode
pytest -v
```

## Database Migrations

### Creating a Migration

```bash
# Auto-generate migration
alembic revision --autogenerate -m "description of changes"

# Edit the generated file in alembic/versions/
# Test migration
alembic upgrade head

# Test rollback
alembic downgrade -1
alembic upgrade head
```

### Migration Guidelines

- Always test migrations on a copy of production data
- Provide rollback capability
- Document any manual steps required
- Include data migration if schema changes
- Never edit existing migrations

## Documentation

### When to Update Docs

- Adding new features
- Changing API endpoints
- Modifying database schema
- Updating deployment process
- Changing configuration

### Documentation Structure

```
docs/
├── requirements/       # Requirements and specifications
├── design/            # Design documents
├── plannings/         # Implementation plans
└── CONTRIBUTING.md    # This file
```

## Questions?

If you have questions:
1. Check existing issues and discussions
2. Review documentation
3. Create a new issue with the `question` label

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to OmniContent! 🚀
