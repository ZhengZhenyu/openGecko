FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（curl 用于健康检查）
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建必要目录
RUN mkdir -p /app/uploads /app/data

# 创建非 root 用户，降低容器权限
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# 开发环境使用 uvicorn，生产通过 docker-compose.prod.yml 覆盖为 gunicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
