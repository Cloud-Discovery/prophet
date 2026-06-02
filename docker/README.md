# Prophet 容器化部署指南

## 概述

本项目使用 Docker 容器化部署，包含以下服务：

- **backend**: 后端服务容器，包含 Flask、Celery Worker 和 Redis
- **frontend**: 前端服务容器，使用 Nginx 提供静态文件服务

## 文件结构

```
.
├── Dockerfile.backend          # 后端容器构建文件
├── Dockerfile.frontend         # 前端容器构建文件
├── docker-compose.yml          # Docker Compose 编排文件
├── .dockerignore               # Docker 构建忽略文件
└── docker/
    ├── backend/
    │   ├── start.sh            # 后端启动脚本
    │   └── supervisord.conf    # Supervisor 配置文件
    └── frontend/
        └── nginx.conf          # Nginx 配置文件
```

## 快速开始

### 1. 环境准备

确保已安装：

- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### 2. 环境变量配置

创建 `.env` 文件（可选，用于覆盖默认配置）：

```bash
# 安全密钥（必须修改）
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# 数据库配置（可选，默认使用 SQLite）
DATABASE_URL=sqlite:///data/prophet.db

# Celery 配置（可选，默认使用容器内 Redis）
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. 构建和启动

```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. 访问应用

- 前端: http://localhost
- 后端 API: http://localhost:5000/api/v1/health

## 服务说明

### 后端服务 (backend)

后端容器运行以下服务：

1. **Redis** (端口 6379)

   - Celery 消息代理和结果后端
   - 仅在容器内部访问

2. **Flask API** (端口 5000)

   - 使用 Gunicorn 运行
   - 4 个工作进程，2 个线程

3. **Celery Worker**
   - 处理异步任务
   - 自动重启

所有服务由 Supervisor 管理，确保服务高可用。

### 前端服务 (frontend)

- 使用 Nginx 提供静态文件服务
- 自动代理 `/api` 请求到后端
- 支持 SPA 路由

## 数据持久化

以下目录通过 volume 挂载，数据会持久化：

- `./data`: 数据库文件
- `./logs`: 日志文件
- `./uploads`: 上传文件

## 常用命令

```bash
# 停止服务
docker-compose down

# 停止并删除 volumes（注意：会删除数据）
docker-compose down -v

# 重启服务
docker-compose restart

# 重启特定服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh

# 查看容器资源使用
docker stats

# 重建镜像（代码更新后）
docker-compose build --no-cache
docker-compose up -d
```

## 健康检查

后端服务包含健康检查端点：

```bash
curl http://localhost:5000/api/v1/health
```

## 故障排查

### 1. 查看日志

```bash
# 所有服务日志
docker-compose logs

# 后端服务日志
docker-compose logs backend

# 实时跟踪日志
docker-compose logs -f backend
```

### 2. 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看容器详细信息
docker inspect prophet-backend
docker inspect prophet-frontend
```

### 3. 进入容器调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 检查 Redis
redis-cli ping

# 检查 Celery
celery -A celery_worker.celery inspect active

# 检查 Supervisor 状态
supervisorctl status
```

### 4. 常见问题

**问题：端口被占用**

```bash
# 修改 docker-compose.yml 中的端口映射
ports:
  - "5000:5000"  # 将主机端口改为 5001
```

**问题：权限问题**

```bash
# 确保挂载目录有正确权限
sudo chown -R $USER:$USER ./data ./logs ./uploads
```

**问题：Redis 连接失败**

```bash
# 检查 Redis 是否在容器内运行
docker-compose exec backend redis-cli ping
```

## 生产环境建议

1. **使用外部数据库**

   - 修改 `DATABASE_URL` 为 PostgreSQL 或 MySQL
   - 确保数据库服务可访问

2. **使用外部 Redis**

   - 修改 `CELERY_BROKER_URL` 和 `CELERY_RESULT_BACKEND`
   - 使用独立的 Redis 容器或服务

3. **配置 HTTPS**

   - 在 Nginx 配置中添加 SSL 证书
   - 使用 Let's Encrypt 或商业证书

4. **设置资源限制**

   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: "2"
             memory: 2G
   ```

5. **配置日志轮转**

   - 使用 Docker 日志驱动
   - 配置日志大小限制

6. **备份策略**
   - 定期备份 `./data` 目录
   - 配置自动备份脚本

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 查看日志确认
docker-compose logs -f
```

## 监控

建议在生产环境中配置监控：

- Prometheus + Grafana
- ELK Stack (日志分析)
- Sentry (错误追踪)

## 支持

如有问题，请查看：

- 项目 README.md
- 日志文件: `./logs/`
- GitHub Issues
