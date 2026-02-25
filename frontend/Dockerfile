# syntax=docker/dockerfile:1
FROM node:20-alpine3.21 AS builder

WORKDIR /app

# 先复制依赖清单（含 lockfile）——这两个文件不变时，下面两步完全走缓存
COPY package.json package-lock.json ./
# --mount=type=cache 让 npm 缓存跨构建复用：即使 package.json 变化也只下载新增包
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline

COPY . .
RUN npm run build

FROM nginx:1.27-alpine3.21

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
