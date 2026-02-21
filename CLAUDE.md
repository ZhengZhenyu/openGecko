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

## Skills

### openGecko LFX 设计系统

**所有前端页面必须遵循 LFX Insights 浅色主题设计规范。** 完整的设计令牌、颜色映射、组件样式、布局规范和检查清单详见 `.claude/skills/opengecko-lfx-design-system.md`。

新建或修改任何前端页面/组件时，务必先阅读该 skill 文件，确保：
- 使用正确的 CSS 变量（`--text-primary: #1e293b`、`--blue: #0095ff` 等）
- 遵循统一的页面 padding、标题字号、卡片阴影规范
- 不使用任何禁止色值（如 `#409EFF`、`#303133`、`--el-color-primary` 等）

## Language

Project documentation and commit messages are in Chinese. Code, comments, and variable names are in English.

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
  - API 端点测试：`tests/test_{module}_api.py`（如 `test_contents_api.py`）
  - 服务层单元测试：`tests/test_services.py`（统一放置所有纯 Python 服务的单元测试）
  - 特定服务测试：`tests/test_{service}_service.py`（如 `test_wechat_service.py`）
- Use pytest as test framework
- Mock external services (WeChat, email, SMTP) with `unittest.mock.patch` or `pytest-mock`
  - 优先用 `mock.patch` 直接 patch service 方法，而非 `httpx_mock` 匹配 URL（URL 参数易变）
- Test both success and error paths
- Test RBAC permissions (admin/user/superuser)
- Test multi-tenant isolation

### Critical Route & Dependency Facts
这些是容易搞错的细节，写测试时务必核对：
- `upload.router` 注册在 `/api/contents` 前缀下，实际路径为 `/api/contents/upload` 和 `/api/contents/{id}/cover`
- `dashboard.router` 注册在 `/api/users/me` 前缀下，实际路径为 `/api/users/me/dashboard`、`/api/users/me/assigned/contents` 等
- `get_current_community` 依赖返回的是 `int`（community_id），**不是** Community 对象
- `Meeting` 模型的 `committee_id` 字段为 NOT NULL，创建 Meeting 时必须先创建 Committee
- `Committee` 模型的 `slug` 字段为 NOT NULL，创建时必须提供 slug
- `conftest.py` 中的 `test_user` 在 `community_users` 表中角色为 `admin`（非 `user`）

### Service Unit Test Patterns
对纯 Python 服务（email、ics、notification、converter 等）编写单元测试时：
- 使用 `MagicMock()` 模拟 SQLAlchemy 模型对象（无需真实数据库）
- SMTP 测试通过 `patch('smtplib.SMTP')` / `patch('smtplib.SMTP_SSL')` 拦截网络调用
- 对 `db.query(Model).filter(...).first()` 链式调用，用 `side_effect` 按 model 类型分发返回值

### Coverage Improvement Checklist
当覆盖率低于 80% 时，优先补充以下模块：
1. `app/services/email.py` - SMTP 发送逻辑（用 mock 拦截 smtplib）
2. `app/services/ics.py` - ICS 格式生成（纯函数，无需 mock）
3. `app/services/notification.py` - 邮件提醒（mock DB + email）
4. `app/services/converter.py` - Markdown/HTML 转换（纯函数）
5. `app/api/dashboard.py` - 个人工作台端点
6. `app/api/upload.py` - 文件上传端点

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
- **在执行 `git push` 操作前，必须先询问用户**："是否现在推送到远程，还是等后续改动一并推送？"，得到明确确认后再执行；`git commit` 可由 AI 自行执行，无需询问

### Pull Request Process
- Create PR from feature branch to develop
- All CI checks must pass
- Request review from at least one maintainer
- Squash commits when merging to develop/main

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

### 分步生成大文件以避免超时

当需要生成较大的代码文件（测试文件、服务文件等，通常 > 200 行）时，**不要试图一次性生成整个文件**，应分步完成：

1. **先创建骨架**：用 `create_file` 写入文件头部、imports 和第一个测试类（~50-80 行）
2. **逐类追加**：用 `replace_string_in_file` 在文件末尾依次追加后续测试类
3. **最后验证**：运行 `pytest tests/该文件.py --no-cov -q` 确认全部通过

```python
# 步骤 1：create_file 写入头部 + 第一个类（~50-80 行）
# 步骤 2：replace_string_in_file 追加第二个类
# 步骤 3：replace_string_in_file 追加第三个类
# ...
# 步骤 N：运行测试验证
```

### 调试测试失败的高效流程

1. 先隔离失败的测试类/函数，避免受其他测试干扰：
   ```bash
   pytest tests/test_xxx.py::ClassName::test_method --no-cov -q --tb=short
   ```
2. 查看实际 HTTP 响应体（不只看 status code）：
   ```python
   print(response.json())  # 临时加入测试中
   ```
3. 检查路由注册前缀（`app/main.py` 中 `include_router` 的 `prefix` 参数）
4. 检查依赖注入返回类型（`get_current_community` 返回 `int`，不是对象）

### 覆盖率未达标时的排查步骤

```bash
# 查看每个文件的未覆盖行
pytest --cov=app --cov-report=term-missing -q 2>&1 | grep -E "[0-9]+%"
```

找到覆盖率低的模块后，优先针对**纯函数**和**独立服务类**补充单元测试（无需 HTTP client，速度快，覆盖率提升效果好）。
