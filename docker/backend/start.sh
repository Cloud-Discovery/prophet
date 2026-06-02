#!/bin/bash
set -e

# 创建必要的目录
mkdir -p /app/data /app/logs /app/uploads

# 初始化数据库（如果需要）
if [ ! -f /app/data/prophet.db ]; then
    echo "Initializing database..."
    python -c "from app import create_app; from db import init_db; app = create_app(); init_db(app)"
fi

# 启动所有服务（由 supervisor 管理）
echo "Starting services with supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

