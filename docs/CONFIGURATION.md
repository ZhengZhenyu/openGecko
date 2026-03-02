# 配置指南

本文档详细说明 openGecko 的所有环境变量（`.env` 配置项）。
配置由 `backend/app/config.py`（Pydantic Settings）统一管理；模板文件可通过以下命令从源代码自动生成：

```bash
cd backend
python scripts/generate_env_example.py          # 重新生成 .env.example
python scripts/generate_env_example.py --prod   # 重新生成 .env.prod.example
python scripts/generate_env_example.py --check  # CI 用：检测 .env.example 是否过时
```

## 快速开始

```bash
# 开发环境
cp backend/.env.example backend/.env

# 生产环境（必须逐项填写 REPLACE_WITH_... 占位符后再部署）
cp backend/.env.prod.example backend/.env
```

## 环境变量配置

### 基础配置

编辑 `backend/.env`：

```env
# 数据库（开发用 SQLite，生产换 PostgreSQL）
DATABASE_URL=sqlite:///./data/opengecko.db

# JWT 密钥（⚠️ 生产必须替换：openssl rand -hex 32）
JWT_SECRET_KEY=change-me-in-production-please-use-a-strong-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 天 = 10080 分钟

# CORS（逗号分隔字符串，非 JSON 数组）
# 开发默认值已内置，生产环境必须显式指定
CORS_ORIGINS=https://your-domain.com
```

### 数据库配置

#### 开发环境 (SQLite)

```env
DATABASE_URL=sqlite:///./opengecko.db
```

#### 生产环境 (PostgreSQL)

```env
DATABASE_URL=postgresql://opengecko:YOUR_PASSWORD@db:5432/opengecko
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800
```

### 速率限制

```env
# 登录端点（防暴力破解），格式：<次数>/<单位>（second/minute/hour）
RATE_LIMIT_LOGIN=10/minute
# 所有 API 默认限制
RATE_LIMIT_DEFAULT=120/minute
```

### 渠道配置说明

> **⚠️ 注意**：微信、Hugo、CSDN、知乎等渠道凭证**不是环境变量**，
> 而是 **per-community 数据库配置**，存储在 `channel_configs` 表中（Fernet 加密）。

通过 UI「设置」→「渠道配置」页面为每个社区单独配置：

| 渠道 | 所需凭证 | 获取方式 |
|------|---------|----------|
| 微信公众号 | AppID + AppSecret | 微信公众平台 → 开发 → 基本配置 |
| Hugo | 博客仓库绝对路径 + 内容目录 | 本地 Hugo 仓库路径 |
| CSDN | Cookie | 浏览器 DevTools → Application → Cookies |
| 知乎 | Cookie | 浏览器 DevTools → Application → Cookies |

所有凭证经 Fernet 对称加密后入库，API 返回时末 4 位脱敏，不以明文传输。

## 社区配置

### 创建社区

通过管理界面创建社区，配置：

- **社区名称**: 显示名称
- **Slug**: URL 友好的唯一标识符
- **描述**: 社区简介
- **Logo URL**: 社区标志图片链接
- **设置**: JSON 格式的自定义配置

### 渠道配置

为每个社区独立配置发布渠道：

```json
{
  "wechat": {
    "enabled": true,
    "app_id": "community_specific_app_id",
    "app_secret": "community_specific_secret"
  },
  "hugo": {
    "enabled": true,
    "repo_path": "/path/to/community/blog",
    "content_dir": "content/posts"
  }
}
```

## 用户管理

### 创建管理员

默认管理员账号：
- 用户名: `admin`
- 密码: `admin123`

**⚠️ 生产环境必须立即修改默认密码！**

### 添加新用户

通过管理界面或 API 创建用户：

```bash
POST /api/auth/register
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "User Full Name"
}
```

### 用户权限

- **超级管理员**: 管理所有社区和用户
- **普通用户**: 只能访问授权的社区

## 安全配置

### JWT 密钥

**生产环境必须修改 JWT 密钥**：

```bash
# 生成随机密钥
openssl rand -hex 32
```

将生成的值设置为 `JWT_SECRET_KEY`。

### CORS 配置

生产环境配置实际的前端域名（**逗号分隔字符串，非 JSON 数组**）：

```env
CORS_ORIGINS=https://your-domain.com,https://admin.your-domain.com
```

## 日志配置

```env
# 可选：debug / info / warning / error / critical
LOG_LEVEL=warning
```

> `LOG_FILE` 不支持环境变量配置。运行时默认输出到 stdout/stderr，
> 建议由 Docker logging driver 或 Nginx 收集日志，生产环境可考虑接入 Loki。

## 文件存储配置

```env
# 存储后端：local（本地文件系统，开发默认）或 s3（S3 兼容对象存储，生产推荐）
STORAGE_BACKEND=local

# 单次上传大小上限（字节），默认 50MB
MAX_UPLOAD_SIZE=52428800
```

> `UPLOAD_DIR` 无需手动设置，由 `config.py` 自动解析为 `backend/uploads/`。
> 允许的文件类型通过代码白名单（`ALLOWED_MIME_TYPES`）控制，不走环境变量。

### S3 / MinIO 对象存储（生产推荐）

```env
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://minio:9000       # MinIO Docker 内网；AWS S3 改为 https://s3.amazonaws.com
S3_ACCESS_KEY=YOUR_ACCESS_KEY
S3_SECRET_KEY=YOUR_SECRET_KEY
S3_BUCKET=opengecko
S3_PUBLIC_URL=http://minio:9000/opengecko  # nginx /uploads/ 代理目标
```

## Docker 配置

编辑 `docker-compose.yml` 自定义部署：

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/opengecko
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=opengecko
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## 可选功能模块

### SMTP 邮件（密码重置和会议通知）

```env
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587              # 587=STARTTLS，465=SSL
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=YOUR_SMTP_PASSWORD
SMTP_FROM_EMAIL=noreply@your-domain.com
SMTP_USE_TLS=true
# 前端地址，用于密码重置邮件中的跳转链接
FRONTEND_URL=https://your-domain.com
```

`SMTP_HOST` 留空则禁用邮件功能（不会报错，仅记录警告日志）。

### 时区配置

```env
APP_TIMEZONE=Asia/Shanghai   # 影响 ICS 日历和邮件通知中的时间显示
```

数据库始终存储 UTC，此配置仅控制服务端输出内容的本地化时区。
IANA 时区列表： https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### 洞察与人脉模块

该模块包含「人脉管理」和「生态洞察」功能，相对独立，可按需启用或禁用。

```env
# 禁用「洞察与人脉」模块（默认 true = 启用）
ENABLE_INSIGHTS_MODULE=false
```

关闭后效果：
- 后端不注册 `/api/people` 和 `/api/ecosystem` 路由（返回 404）
- 前端侧边栏隐藏「洞察与人脉」菜单
- 直接访问 `/people`、`/ecosystem` 等 URL 自动跳转至首页
- 数据库表保留，随时可重新开启

### 生态洞察自动采集服务（可选容器）

需单独启动 `collector` profile：

```bash
# 启动完整版（含自动采集）
docker compose --profile collector up -d
```

相关环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GITHUB_TOKEN` | 空 | GitHub Personal Access Token；不填则受 60 req/h 匿名限速 |
| `GITEE_TOKEN` | 空 | Gitee 私人令牌（可选） |
| `COLLECTOR_SYNC_INTERVAL_HOURS` | `24` | 全局默认采集间隔（小时），各项目可单独覆盖 |
| `COLLECTOR_MAX_PROJECTS_PER_RUN` | `20` | 每次运行最多同步项目数，防止触发 API 速率限制 |

各项目的采集间隔可在「生态洞察 → 项目信息」页面单独设置，`null` 表示使用全局默认值。

## 故障排查

### 数据库连接失败

检查 DATABASE_URL 格式和数据库服务状态：

```bash
# SQLite: 确保路径可写
ls -la backend/

# PostgreSQL: 测试连接
psql $DATABASE_URL
```

### 微信公众号 API 报错

- 检查 AppID 和 AppSecret 是否正确
- 确认 IP 白名单配置
- 查看微信公众平台接口调用日志

### Hugo 发布失败

- 检查「设置」→「渠道配置」中 Hugo 仓库路径是否为绝对路径
- 确认 FastAPI 进程用户对该目录有读写权限
- 验证目标目录中存在有效 Git 仓库（`git -C /path/to/repo status`）

## 性能优化

### 数据库连接池

```env
DB_POOL_SIZE=10        # 常驻连接数
DB_MAX_OVERFLOW=20     # pool_size 耗尽后最多新开的连接
DB_POOL_TIMEOUT=30     # 等待连接超时（秒）
DB_POOL_RECYCLE=1800   # 30 分钟回收连接，防止 DB 断开
```

> 当前版本无独立缓存层（无 Redis），热点数据直接走 DB，需确保连接池配置合理。
> 扩展阶段可引入 Redis 缓存，详见架构设计文档。

## 备份配置

### 自动备份

配置定时备份任务：

```bash
# 添加到 crontab
0 2 * * * /path/to/backup-script.sh
```

示例备份脚本：

```bash
#!/bin/bash
BACKUP_DIR=/path/to/backups
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
cp backend/opengecko.db $BACKUP_DIR/opengecko_$DATE.db

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz backend/uploads/

# 删除 30 天前的备份
find $BACKUP_DIR -mtime +30 -delete
```
