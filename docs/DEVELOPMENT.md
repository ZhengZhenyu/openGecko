# 开发指南

本文档提供 OmniContent 的开发环境设置、工作流程和最佳实践。

## 环境要求

### 必需

- **Python**: 3.11+
- **Node.js**: 18+
- **Git**: 2.x

### 推荐

- **Docker**: 用于容器化开发和部署
- **Make**: 简化常用命令

### macOS 安装

```bash
brew install python@3.11 node git
```

### Linux 安装

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 nodejs npm git

# Fedora/RHEL
sudo dnf install python3.11 nodejs git
```

## 项目设置

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/omnicontent.git
cd omnicontent
```

### 2. 一键安装 (推荐)

```bash
make setup
```

这会自动：
- 安装后端 Python 依赖
- 安装前端 Node.js 依赖
- 创建数据库并运行迁移
- 初始化配置文件

### 3. 手动安装

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
alembic upgrade head

# 创建初始数据 (可选)
python scripts/seed_data.py
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量 (可选)
cp .env.example .env
```

## 开发服务器

### 使用 Make (推荐)

```bash
# 同时启动前后端
make dev

# 只启动后端
make dev-backend

# 只启动前端
make dev-frontend

# 停止所有服务
make stop
```

### 手动启动

#### 后端 (FastAPI)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

访问:
- API: http://localhost:8000
- 交互式文档: http://localhost:8000/docs
- OpenAPI Schema: http://localhost:8000/openapi.json

#### 前端 (Vue)

```bash
cd frontend
npm run dev
```

访问: http://localhost:3000

## Make 命令参考

| 命令 | 说明 |
|------|------|
| `make setup` | 安装所有依赖并初始化数据库 |
| `make dev` | 启动前后端开发服务器 |
| `make dev-backend` | 只启动后端服务 |
| `make dev-frontend` | 只启动前端服务 |
| `make test` | 运行所有测试 |
| `make test-backend` | 运行后端测试 |
| `make test-frontend` | 运行前端测试 |
| `make lint` | 代码格式检查 |
| `make format` | 自动格式化代码 |
| `make clean` | 清理构建产物和缓存 |
| `make stop` | 停止后台服务 |
| `make migration name="description"` | 创建新的数据库迁移 |

## 测试

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 运行带覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 前端测试

```bash
cd frontend

# 单元测试
npm run test:unit

# E2E 测试
npm run test:e2e

# 覆盖率报告
npm run test:coverage
```

### CI/CD

项目使用 GitHub Actions 自动运行测试：

- **Backend CI**: 代码检查、测试、安全扫描
- **Frontend CI**: 构建、测试、类型检查
- **Migration Check**: 数据库迁移验证

查看 `.github/workflows/` 了解详细配置。

## 代码规范

### 后端 (Python)

使用 **ruff** 和 **black** 进行代码检查和格式化：

```bash
cd backend

# 代码检查
ruff check app/

# 自动格式化
black app/

# 类型检查
mypy app/
```

**编码规范**:
- 遵循 PEP 8
- 使用类型注解 (Type Hints)
- 编写 Docstrings (Google 风格)
- 最大行长度: 100 字符

### 前端 (TypeScript/Vue)

使用 **ESLint** 和 **Prettier**：

```bash
cd frontend

# 代码检查
npm run lint

# 自动修复
npm run lint:fix

# 格式化
npm run format
```

**编码规范**:
- 使用 TypeScript
- Vue 3 Composition API
- 组件命名: PascalCase
- 文件命名: kebab-case

## 数据库迁移

使用 **Alembic** 管理数据库 schema 变更。

### 创建迁移

```bash
cd backend

# 自动生成迁移
alembic revision --autogenerate -m "Add user avatar field"

# 手动创建迁移
alembic revision -m "Create custom index"
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade <revision_id>

# 回退一个版本
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 迁移最佳实践

- ✅ 始终测试迁移的 upgrade 和 downgrade
- ✅ 包含数据迁移逻辑 (如需要)
- ✅ 为外键和约束命名
- ✅ 在 CI 中验证迁移可执行
- ❌ 不要编辑已提交的迁移文件

## Git 工作流

### 分支策略

- `main`: 稳定的生产代码
- `develop`: 开发分支
- `feature/*`: 新功能分支
- `fix/*`: Bug 修复分支

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add calendar view drag and drop
fix: resolve JWT token expiration issue
docs: update configuration guide
style: format code with black
refactor: extract auth logic to service layer
test: add tests for community CRUD
chore: update dependencies
```

### 提交前检查

```bash
# 运行测试
make test

# 代码检查
make lint

# 格式化代码
make format
```

### Pull Request

1. 创建功能分支
2. 完成开发和测试
3. 提交 PR 到 `develop`
4. 等待 CI 通过
5. Code Review
6. 合并到 `develop`

## API 开发

### FastAPI 路由结构

```
backend/app/api/
├── __init__.py
├── auth.py          # 认证相关
├── communities.py   # 社区管理
├── contents.py      # 内容管理
├── channels.py      # 渠道配置
└── analytics.py     # 数据分析
```

### 创建新端点

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, get_current_community
from app.models.user import User

router = APIRouter(prefix="/api/example", tags=["example"])

@router.get("/items")
async def get_items(
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
):
    """Get items for current community."""
    # 实现逻辑
    return {"items": []}
```

### API 文档

FastAPI 自动生成 OpenAPI 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 前端开发

### 项目结构

```
frontend/src/
├── assets/          # 静态资源
├── components/      # 可复用组件
├── views/           # 页面组件
├── router/          # 路由配置
├── stores/          # Pinia 状态管理
├── api/             # API 客户端
├── types/           # TypeScript 类型
└── utils/           # 工具函数
```

### 添加新页面

1. 创建 Vue 组件在 `views/`
2. 在 `router/index.ts` 添加路由
3. 如需状态管理，在 `stores/` 创建 Store
4. 在 `api/` 添加 API 调用

### 组件开发

```vue
<script setup lang="ts">
import { ref } from 'vue'
import type { Content } from '@/types/content'

const props = defineProps<{
  contentId: number
}>()

const emit = defineEmits<{
  (e: 'update', content: Content): void
}>()

const content = ref<Content>()
</script>

<template>
  <div class="content-card">
    {{ content?.title }}
  </div>
</template>

<style scoped>
.content-card {
  /* 样式 */
}
</style>
```

## 调试

### 后端调试

使用 VS Code launch.json:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### 前端调试

使用 Vue DevTools:

```bash
# Chrome 扩展
# https://chrome.google.com/webstore/detail/vuejs-devtools
```

## 常见问题

### 后端依赖安装失败

```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 前端依赖安装失败

```bash
# 清理缓存
npm cache clean --force

# 使用国内镜像
npm install --registry=https://registry.npmmirror.com
```

### 数据库迁移失败

```bash
# 检查当前版本
alembic current

# 查看迁移历史
alembic history

# 强制标记到特定版本 (谨慎使用)
alembic stamp head
```

### 端口占用

```bash
# 查找占用端口的进程
lsof -i :8000  # 后端
lsof -i :3000  # 前端

# 终止进程
kill -9 <PID>
```

## 生产部署

详见 [部署文档](DEPLOYMENT.md)。

## 资源链接

### 框架文档

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue 3](https://vuejs.org/)
- [Pinia](https://pinia.vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)

### 工具

- [FullCalendar](https://fullcalendar.io/docs/vue)
- [ECharts](https://echarts.apache.org/)
- [vue-draggable-plus](https://alfred-skyblue.github.io/vue-draggable-plus/)

### 代码规范

- [PEP 8](https://peps.python.org/pep-0008/)
- [Vue Style Guide](https://vuejs.org/style-guide/)
- [Conventional Commits](https://www.conventionalcommits.org/)
