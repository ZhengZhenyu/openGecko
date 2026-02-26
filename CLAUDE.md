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

## Frontend Design Standards

All frontend pages **must** follow the **LFX Insights light theme**. Full reference: `.claude/skills/opengecko-frontend-design/SKILL.md`.

### Design Tokens

Declare CSS variables on the **component root selector** (never on `:root`):

```css
.page-root {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --green:          #22c55e;
  --orange:         #f59e0b;
  --red:            #ef4444;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;
}
```

### Color Reference

| Purpose | Value | Variable |
|---------|-------|----------|
| Page background | `#f5f7fa` | — (set in `App.vue .app-main`) |
| Card / white background | `#ffffff` | — |
| Primary text | `#1e293b` | `--text-primary` |
| Secondary text | `#64748b` | `--text-secondary` |
| Muted text | `#94a3b8` | `--text-muted` |
| Brand blue | `#0095ff` | `--blue` |
| Brand blue hover | `#0080e6` | — |
| Success green | `#22c55e` | `--green` |
| Warning orange | `#f59e0b` | `--orange` |
| Danger red | `#ef4444` | `--red` |
| Border | `#e2e8f0` | `--border` |
| Divider | `#f1f5f9` | — |
| Subtle background | `#f8fafc` | — |
| Blue tint background | `#eff6ff` | — |
| Green tint background | `#f0fdf4` | — |
| Orange tint background | `#fffbeb` | — |
| Red tint background | `#fef2f2` | — |

### Layout

```css
/* Page container */
.page-root {
  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Page title row */
.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-title-row h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-title-row .subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

/* Section card */
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}
.section-card:hover {
  box-shadow: var(--shadow-hover);
}

/* Section header (no border-bottom) */
.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
```

### Responsive Breakpoints

```css
@media (max-width: 1200px) {
  .page-root { padding: 28px 24px; }
}
@media (max-width: 734px) {
  .page-root { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
}
```

### Components

#### Badges / Tags
- Border-radius: `6px`; **no border**
- Use light-background + dark-text pairs:
  - Blue: `background: #eff6ff; color: #1d4ed8`
  - Green: `background: #f0fdf4; color: #15803d`
  - Orange: `background: #fffbeb; color: #b45309`
  - Gray: `background: #f1f5f9; color: #64748b`
  - Red: `background: #fef2f2; color: #dc2626`

#### Buttons

```css
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s ease;
}
/* Primary */
:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}
:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}
/* Default */
:deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}
:deep(.el-button--default:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}
```

- **Never** use `transform: translateY()` on hover
- Text-link buttons use `link` attribute; hover adds a subtle background tint
- **Avoid** applying `:deep(.el-button--primary)` background overrides that unintentionally affect `text` type buttons — use custom CSS classes or `<span>` wrappers instead

#### Inputs

```css
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
```

#### Tables

```css
:deep(.el-table th) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
:deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
}
:deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}
```

#### Dialogs

```css
:deep(.el-dialog) { border-radius: var(--radius); }
:deep(.el-dialog__header) { border-bottom: 1px solid #f1f5f9; }
```

#### Pagination

```css
:deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}
```

### Sidebar (App.vue)

- Background: `#ffffff`; right border: `1px solid #e2e8f0`
- Logo area: white background + `border-bottom: 1px solid #e2e8f0`
- Menu item text: `#64748b`; active: `#0095ff`
- Menu item hover: `background: #f8fafc; color: #1e293b`
- Menu item active: `background: #eff6ff; color: #0095ff`
- Menu item border-radius: `8px`; margin: `2px 8px`
- `el-menu` inline props: `background-color="#ffffff"` `text-color="#64748b"` `active-text-color="#0095ff"`

### Forbidden Colors

Never use these — they are Element Plus defaults or old dark-theme remnants:

| Forbidden | Replace with |
|-----------|-------------|
| `#409EFF` | `var(--blue)` (#0095ff) |
| `#303133` | `var(--text-primary)` (#1e293b) |
| `#606266` | `var(--text-secondary)` (#64748b) |
| `#909399` | `var(--text-muted)` (#94a3b8) |
| `#dcdfe6` / `#ebeef5` | `var(--border)` (#e2e8f0) |
| `#0071e3` | `var(--blue)` (#0095ff) |
| `#1d2129` | `var(--text-primary)` (#1e293b) |
| `#86909c` | `var(--text-secondary)` (#64748b) |
| `--el-color-primary` | `var(--blue)` |
| `--el-text-color-*` | corresponding `--text-*` variable |
| `--el-fill-color-*` | `#f8fafc` or `#f1f5f9` |
| `--el-border-color` | `var(--border)` |

### Design Checklist

When creating or modifying any page:

- [ ] CSS variables declared on component root selector (not `:root`)
- [ ] Page padding: `32px 40px 60px`; max-width: `1400px`
- [ ] `h2`: `28px / 700 / letter-spacing: -0.02em`
- [ ] Subtitle: `15px / var(--text-secondary)`
- [ ] Cards use `--border` + `--shadow` + `--radius`
- [ ] Buttons: `border-radius: 8px`, `transition: 0.15s ease`
- [ ] No `transform: translateY` hover effects
- [ ] Badges/Tags: no border, light-bg + dark-text
- [ ] No forbidden colors
- [ ] Element Plus overrides use `:deep()` syntax
- [ ] No `lang="scss"` unless required for deep overrides (prefer plain CSS)

## Contributing to Upstream (Issue + PR Workflow)

When a user asks to submit work to the upstream repository (`opensourceways/openGecko`) — phrases like "create a PR", "open a PR", "submit to upstream", "提 PR" — **always use the `github-pr` skill** (`/github-pr`).

### What the skill does

1. **Auto-detects fork identity** from `git remote get-url origin` — no username is ever hardcoded.
2. **Creates an issue** on `opensourceways/openGecko` describing the feature/fix.
3. **Squashes all commits into one** before pushing — the upstream CI bot adds a `needs-squash` label that **blocks merging** when a PR has more than one commit.
4. **Pushes the branch** to the contributor's fork (rebases first if fork is ahead).
5. **Creates a PR** from `{fork_user}:{branch}` → `opensourceways/openGecko:main` with `Closes #<issue>` in the body.

> **`needs-squash` quick fix**: if the label is added to an existing PR, run:
> ```bash
> git reset --soft upstream/main
> git commit -m 'type: message'
> git push origin <branch> --force-with-lease
> ```

### Remote conventions

| Remote | Points to |
|--------|-----------|
| `upstream` | `opensourceways/openGecko` (canonical repo) |
| `origin` | contributor's personal fork |

If `upstream` is not configured, add it:

```bash
git remote add upstream https://github.com/opensourceways/openGecko.git
```

### Skill reference

Full workflow details: `.claude/skills/github-pr/SKILL.md`

---

## Language

Commit messages and user-facing strings are in Chinese. Code, variable names, comments, and this file are in English.

## Security Coding Standards

### Input Validation
- Use Pydantic models for all request/response validation
- Never trust client input; always validate with Pydantic schemas
- Use `str` with `min_length`/`max_length` constraints
- Use `EmailStr` for email validation
- Use `HttpUrl` for URL validation
- Use `conint`/`confloat` for numeric ranges

### SQL Injection Prevention
- Use SQLAlchemy ORM exclusively; never construct raw SQL queries with user input
- If raw SQL is absolutely necessary, use `text()` with parameter binding
- Never use f-strings or string concatenation for SQL queries

### XSS Prevention
- Frontend: Vue 3 automatically escapes template expressions
- Use `v-html` only with trusted content
- For rich text, sanitize HTML before rendering (use DOMPurify or similar)

### File Upload Security
- Validate file types using whitelist (extension + MIME type)
- Restrict file size (max 10MB by default)
- Generate random filenames to prevent path traversal
- Store uploads outside web root; serve via dedicated endpoint

### Sensitive Data Encryption
- Use Fernet for encrypting sensitive data (e.g., channel credentials)
- Key derived from `JWT_SECRET_KEY` in config
- Never log sensitive data (passwords, tokens, API keys)
- Use environment variables for secrets; never commit to repo

### OWASP Checklist
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (ORM only)
- [ ] XSS protection (Vue auto-escape)
- [ ] CSRF protection (JWT in header)
- [ ] Authentication on all protected routes
- [ ] Authorization checks (RBAC)
- [ ] Secure file uploads
- [ ] Sensitive data encryption
- [ ] No hardcoded secrets
- [ ] Security headers (CORS, CSP)

## Backend Coding Standards

### Naming Conventions
- Files and directories: `snake_case.py`
- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Directory Responsibilities
- `api/`: FastAPI routers only; no business logic
- `services/`: Business logic, external integrations
- `models/`: SQLAlchemy ORM models only
- `schemas/`: Pydantic validation schemas
- `core/`: Security, dependencies, utilities
- Keep routers thin; delegate to services

### Multi-Tenant Standards
- All community-scoped queries MUST filter by `community_id`
- Use `Depends(get_current_community)` to enforce isolation
- Never expose data from other communities
- Audit all multi-tenant operations

### Error Handling
- Use `HTTPException` for HTTP errors (FastAPI)
- Never use bare `except:`; always specify exception type
- Log errors with context using structured logging
- Return consistent error format: `{"detail": "error message"}`
- Use status codes appropriately (400, 401, 403, 404, 422, 500)

### Type Hints
- All functions must have type hints
- Use Pydantic models for complex types
- Use `Optional[T]` for nullable fields
- Use `List[T]`, `Dict[K, V]` for collections

## Frontend Coding Standards

### Vue 3 Composition API
- Use `<script setup lang="ts">` syntax exclusively
- Prefer Composition API over Options API
- Use `ref` for primitives, `reactive` for objects
- Use `computed` for derived state
- Use `watch`/`watchEffect` for side effects

### Props and Emits
- Define props with `defineProps<T>()` and type interface
- Define emits with `defineEmits<T>()` and type interface
- Always specify required/optional for props
- Use descriptive emit names (e.g., `update:modelValue`, `submit`)

### Pinia State Management
- Use Pinia stores for global state (auth, community, user)
- Keep stores focused; split by domain
- Use TypeScript for store typing
- Prefer composition stores (`defineStore` with setup function)

### API Calls
- All API calls must be in `frontend/src/api/` directory
- Use Axios with configured interceptors (auto-attach JWT and X-Community-Id)
- Handle errors consistently; show user-friendly messages
- Use async/await; avoid Promise chains

### Element Plus Component Usage
- Use `el-form` with `:model` and `:rules` for validation
- Use `el-table` with proper typing for columns
- Use `el-dialog` with `v-model` for visibility
- Use `el-message`/`el-notification` for feedback
- Follow Element Plus design patterns

### TypeScript Best Practices
- Enable strict mode in `tsconfig.json`
- Avoid `any`; use `unknown` if type is truly unknown
- Use type guards for runtime type checking
- Prefer `interface` over `type` for object shapes

## Testing Requirements

### Backend Testing
- **Minimum 80% code coverage required** — CI will fail if total coverage drops below 80%
- Run full suite with coverage: `pytest --cov=app --cov-report=term-missing -q`
- Test naming conventions:
  - API endpoint tests: `tests/test_{module}_api.py` (e.g., `test_contents_api.py`)
  - Service unit tests: `tests/test_services.py` (all pure-Python service unit tests in one file)
  - Specific service tests: `tests/test_{service}_service.py` (e.g., `test_wechat_service.py`)
- Use pytest as test framework
- Mock external services (WeChat, email, SMTP) with `unittest.mock.patch` or `pytest-mock`
  - Prefer `mock.patch` to directly patch service methods rather than `httpx_mock` URL matching (URLs change easily)
- Test both success and error paths
- Test RBAC permissions (admin/user/superuser)
- Test multi-tenant isolation

### Critical Route & Dependency Facts

These are easy-to-miss details — always verify when writing tests:

- `upload.router` is registered under `/api/contents` prefix; actual paths are `/api/contents/upload` and `/api/contents/{id}/cover`
- `dashboard.router` is registered under `/api/users/me` prefix; actual paths are `/api/users/me/dashboard`, `/api/users/me/assigned/contents`, etc.
- `get_current_community` dependency returns `int` (community_id), **not** a Community object
- `Meeting` model's `committee_id` is NOT NULL; must create a Committee before creating a Meeting
- `Committee` model's `slug` is NOT NULL; must provide slug on creation
- `test_user` in `conftest.py` has role `admin` in `community_users` (not `user`)

### Service Unit Test Patterns

When writing unit tests for pure Python services (email, ics, notification, converter, etc.):
- Use `MagicMock()` to simulate SQLAlchemy model objects (no real database needed)
- Intercept SMTP calls via `patch('smtplib.SMTP')` / `patch('smtplib.SMTP_SSL')`
- For `db.query(Model).filter(...).first()` chain calls, use `side_effect` to dispatch return values by model type

### Coverage Improvement Checklist

When coverage falls below 80%, prioritize adding tests for:
1. `app/services/email.py` — SMTP send logic (intercept smtplib with mock)
2. `app/services/ics.py` — ICS format generation (pure functions, no mock needed)
3. `app/services/notification.py` — email reminders (mock DB + email)
4. `app/services/converter.py` — Markdown/HTML conversion (pure functions)
5. `app/api/dashboard.py` — personal dashboard endpoints
6. `app/api/upload.py` — file upload endpoints

### Frontend Testing
- Unit tests for utilities and stores
- Component tests for key components
- E2E tests for critical user flows
- Use Vitest for unit testing
- Use Playwright for E2E testing

### Test Data
- Use fixtures for test data
- Clean up test data after each test
- Use factories for complex objects

## Git Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/{description}`: New features
- `fix/{description}`: Bug fixes
- `hotfix/{description}`: Critical production fixes

### Commit Message Format
- Use conventional commits:
  - `feat:`: New feature
  - `fix:`: Bug fix
  - `docs:`: Documentation
  - `refactor:`: Code refactoring
  - `test:`: Test changes
  - `chore:`: Build/config changes
- Subject line: 50 chars max
- Body: Explain what and why, not how
- Write commit messages in Chinese

### Commit Guidelines
- Do NOT add `Co-Authored-By:` in commit messages
- Make atomic commits (one logical change per commit)
- Run tests before committing
- Run linting before committing
- **Ask before running `git push`**: confirm whether to push now or wait for more changes to batch; `git commit` can be executed without asking

### Pull Request Process
- Create PR from feature branch to develop
- All CI checks must pass
- Request review from at least one maintainer
- Squash commits when merging to develop/main
- **Upstream PRs must contain exactly one commit** — the upstream CI adds a `needs-squash` label that blocks merging if there are multiple commits. Use `git reset --soft upstream/main && git commit` to squash before pushing.

## API Design Standards

### RESTful Conventions
- Use nouns for resource names (plural)
- Use HTTP verbs appropriately:
  - `GET`: Retrieve data
  - `POST`: Create resource
  - `PUT`/`PATCH`: Update resource
  - `DELETE`: Remove resource
- Use kebab-case for endpoint paths
- Version APIs: `/api/v1/...` (future-proofing)

### Pagination Format
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```
- Query params: `?page=1&page_size=20`
- Default `page_size`: 20
- Max `page_size`: 100

### Error Response Format
```json
{
  "detail": "Error message in Chinese",
  "error_code": "VALIDATION_ERROR",
  "field": "email"
}
```
- Use HTTP status codes appropriately
- Provide user-friendly error messages in Chinese
- Include error codes for programmatic handling

### Success Response Format
- `GET`: Return resource or list
- `POST`: Return created resource (201)
- `PUT`/`PATCH`: Return updated resource
- `DELETE`: Return 204 No Content (or confirmation message)

## Database Migration Guide

### Migration Workflow
1. Modify SQLAlchemy models in `backend/app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file in `backend/alembic/versions/`
4. Apply migration: `alembic upgrade head`
5. Test both upgrade and downgrade

### Migration Best Practices
- Always review auto-generated migrations
- Provide clear, descriptive messages
- Ensure migrations are reversible (implement `downgrade()`)
- Test migrations on both SQLite and PostgreSQL
- Never modify applied migrations; create new ones
- Keep migrations small and focused

### SQLite vs PostgreSQL Compatibility
- Use SQLAlchemy types that work with both databases
- Avoid database-specific features in models
- Test migrations on both databases before merging
- Use Alembic batch mode for SQLite schema changes

## Claude Code Workflow Tips

### Generating Large Files Incrementally

When generating larger code files (test files, service files, typically > 200 lines), **do not attempt to generate the entire file at once**; work in steps:

1. **Create the skeleton first**: write file header, imports, and the first class (~50–80 lines)
2. **Append class by class**: use `replace_string_in_file` to append subsequent classes to the end
3. **Verify at the end**: run `pytest tests/that_file.py --no-cov -q` to confirm all pass

### Debugging Test Failures Efficiently

1. Isolate the failing test first to avoid interference from other tests:
   ```bash
   pytest tests/test_xxx.py::ClassName::test_method --no-cov -q --tb=short
   ```
2. Inspect the actual HTTP response body (not just the status code):
   ```python
   print(response.json())  # add temporarily in the test
   ```
3. Check route registration prefix (`prefix` param in `include_router` in `app/main.py`)
4. Check dependency injection return types (`get_current_community` returns `int`, not an object)

### Diagnosing Low Coverage

```bash
# Show uncovered lines per file
pytest --cov=app --cov-report=term-missing -q 2>&1 | grep -E "[0-9]+%"
```

After finding low-coverage modules, prioritize unit tests for **pure functions** and **standalone service classes** (no HTTP client needed, fast, high coverage gain per test).

### Frontend-Backend Schema Field Name Consistency

**Root cause**: when backend Pydantic schema field names differ from frontend TypeScript interface field names, the API returns JSON with the fields present but the frontend reads `undefined`, causing blank pages or stuck loading (e.g., skeleton screen never disappears). These bugs produce no console errors and are very hard to diagnose.

**Golden rule: the frontend interface is the source of truth — backend schema field names must match exactly.**

#### Principles

1. **Read the frontend before creating a new schema**: before creating a schema in `backend/app/schemas/`, check the corresponding interface in `frontend/src/api/` and ensure field names match exactly.

2. **Consistent naming style**:
   - Use descriptive nouns: `reviewing_contents`, `total_members`, `upcoming_meetings`
   - Avoid redundant suffixes: `pending_review_contents`, `members_count` (vs `total_members`)
   - Do not mix `_count`/`_counts` suffixes with `total_` prefix

3. **Update tests when renaming fields**: after changing schema field names, update all assertions in `tests/` that reference those fields, otherwise CI will fail.

4. **Checklist for diagnosing blank/stuck pages**:
   ```bash
   # 1. Call backend API directly and print field names
   curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/xxx \
     | python3 -m json.tool | grep -E '"[a-z_]+":' | head -20
   # 2. Compare with the field definitions in frontend/src/api/*.ts
   # 3. List all mismatched field names and fix backend schema and API construction
   ```

#### Common Error Reference

| Frontend interface | Wrong backend field | Correct backend field |
|---|---|---|
| `reviewing_contents` | `pending_review_contents` | `reviewing_contents` |
| `total_committees` | `committees_count` | `total_committees` |
| `total_members` | `members_count` | `total_members` |
| `upcoming_meetings` | `upcoming_meetings_count` | `upcoming_meetings` |
| `active_channels` | `active_channels_count` | `active_channels` |
| `monthly_trend` | `publish_trend` | `monthly_trend` |
