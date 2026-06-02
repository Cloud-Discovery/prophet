.PHONY: build up down restart logs clean help

# 默认目标
help:
	@echo "Prophet Docker 部署命令"
	@echo ""
	@echo "可用命令:"
	@echo "  make build      - 构建所有镜像"
	@echo "  make up         - 启动所有服务"
	@echo "  make down       - 停止所有服务"
	@echo "  make restart    - 重启所有服务"
	@echo "  make logs       - 查看所有服务日志"
	@echo "  make clean      - 清理所有容器和镜像"
	@echo "  make rebuild    - 重新构建并启动"

# 构建镜像
build:
	docker-compose build

# 启动服务
up:
	docker-compose up -d

# 停止服务
down:
	docker-compose down

# 重启服务
restart:
	docker-compose restart

# 查看日志
logs:
	docker-compose logs -f

# 清理
clean:
	docker-compose down -v
	docker system prune -f

# 重新构建并启动
rebuild: down build up logs

