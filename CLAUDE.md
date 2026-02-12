# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

openGecko is a multi-tenant open source community management and operation platform. It covers content management with multi-channel publishing (WeChat, Hugo, CSDN, Zhihu), governance (committee management, meeting scheduling), member/personnel management, analytics, and RBAC with 3-tier roles (superuser/admin/user).

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic 2.x
- **Frontend**: Vue 3, TypeScript, Pinia, Element Plus, Vite, Axios
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Deployment**: Docker Compose, Nginx

## Common Commands

```bash
# Setup
make setup                    # One-command setup (backend + frontend)

# Development
make dev                      # Start both servers concurrently
make dev-backend              # FastAPI on localhost:8000
make dev-frontend             # Vite on localhost:3000

# Backend testing
cd backend
pytest                        # All tests
pytest tests/test_auth_api.py # Single test file
pytest -v --cov=app           # With coverage (80% required)

# Backend code quality
black app/                    # Format (line-length=120)
ruff check app/               # Lint
mypy app/                     # Type check

# Database migrations
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Frontend
cd frontend
npm run dev                   # Dev server (port 3000)
npm run build                 # Production build with type checking

# Docker
docker compose up -d          # Production deployment
```

## Architecture

### Multi-Tenant Data Isolation

All community-scoped data uses `community_id` column filtering. The frontend sends `X-Community-Id` header on every request. Backend enforces isolation via FastAPI dependency injection (`get_current_community` in `backend/app/core/dependencies.py`).

### Backend Structure (backend/app/)

- **api/**: FastAPI routers (auth, communities, contents, publish, channels, committees, meetings, analytics, dashboard, upload)
- **models/**: SQLAlchemy ORM models — 10+ tables including users, communities, community_users, contents, content_collaborators, content_assignees, publish_records, channel_configs, audit_logs, committees, meetings
- **schemas/**: Pydantic request/response validation
- **services/**: Business logic — content conversion (converter.py), publishing integrations (wechat.py, hugo.py, csdn.py, zhihu.py), email (email.py, notification.py), calendar export (ics.py)
- **core/**: Security (JWT, bcrypt, Fernet encryption) and dependency injection (auth, RBAC, permissions)
- **config.py**: Pydantic Settings from .env
- **database.py**: DB connection, session management, auto-init with default admin

### Frontend Structure (frontend/src/)

- **api/**: Axios client modules with interceptors (auto-attaches JWT token and X-Community-Id)
- **stores/**: Pinia stores (auth, community, user)
- **views/**: 21 page components
- **router/**: Vue Router with auth guards
- **components/**: Shared components (CommunitySwitcher, RoleBadge, MemberCard)

### Key Patterns

- **RBAC permissions**: Checked via FastAPI `Depends()` — see `get_current_active_superuser`, `get_community_admin`, `check_content_edit_permission` in dependencies.py
- **Content ownership**: `owner_id` (transferable) + `created_by_user_id` (immutable) + `collaborators` (many-to-many). Edit allowed for owner, collaborators, community admins, superusers
- **Channel credentials**: Encrypted with Fernet (key derived from JWT_SECRET_KEY) in channel_configs table
- **Audit logging**: All critical operations logged to audit_logs table with user, community, action, resource details
- **Vite proxy**: `/api` and `/uploads` proxied to backend at localhost:8000

### Content Workflow States

`draft` → `reviewing` → `approved` → `published`

Work status tracked separately via `work_status` field.

## Database Migrations

Migration files are in `backend/alembic/versions/`. Always use `alembic revision --autogenerate` after model changes and review the generated migration before applying.

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- `backend-ci.yml`: Python lint + test
- `frontend-ci.yml`: Build + type check
- `pr-checks.yml`: PR validation
- `database-migration-check.yml`: Alembic migration validation

## Pre-commit Hooks

Configured in `.pre-commit-config.yaml`: black, isort, flake8, mypy, bandit (backend); eslint, prettier (frontend); detect-secrets, no direct commits to main/develop.

## Language

Project documentation and commit messages are in Chinese. Code, comments, and variable names are in English.
