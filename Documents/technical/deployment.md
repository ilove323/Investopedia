# 部署运维指南

> **阅读时间**: 20分钟  
> **难度**: ⭐⭐⭐  
> **前置知识**: Docker基础、Linux命令、网络配置

---

## 📖 目录

- [概述](#概述)
- [环境要求](#环境要求)
- [本地部署](#本地部署)
- [Docker部署](#docker部署)
- [生产环境部署](#生产环境部署)
- [配置管理](#配置管理)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)
- [备份和恢复](#备份和恢复)
- [最佳实践](#最佳实践)

---

## 概述

### 部署架构

```
┌──────────────────────────────────────────────┐
│            Load Balancer (可选)               │
│              Nginx / Traefik                  │
└────────────────┬─────────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │   Streamlit App         │  端口 8501
    │   (policy_system_app)   │
    └────────────┬────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼──────┐         ┌───────▼─────┐
│ RAGFlow  │         │   Whisper   │
│  :9380   │         │    :9000    │
└──────────┘         └─────────────┘
```

### 部署方式对比

| 方式 | 难度 | 适用场景 | 优点 | 缺点 |
|------|------|---------|------|------|
| **本地开发** | ⭐ | 开发测试 | 快速启动 | 依赖本地环境 |
| **Docker Compose** | ⭐⭐ | 单机生产 | 一键部署、隔离环境 | 单点故障 |
| **Kubernetes** | ⭐⭐⭐⭐ | 大规模生产 | 高可用、自动扩容 | 配置复杂 |

---

## 环境要求

### 硬件要求

**最低配置** (测试环境):
```
CPU: 2核
内存: 4GB
磁盘: 20GB SSD
网络: 10Mbps
```

**推荐配置** (生产环境):
```
CPU: 4核+
内存: 8GB+
磁盘: 100GB SSD
网络: 100Mbps
```

### 软件要求

```bash
# 操作系统
Ubuntu 20.04+ / CentOS 8+ / macOS 12+

# Python
Python 3.8+
pip 21.0+

# Docker (可选)
Docker 20.10+
Docker Compose 2.0+

# 其他
Git 2.0+
```

---

## 本地部署

### 1. 克隆代码

```bash
git clone <repository-url>
cd Investopedia
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置系统

```bash
# 复制配置模板
cp config/config.ini.template config/config.ini

# 编辑配置文件
vim config/config.ini
```

**必须配置的项**:
```ini
[RAGFLOW]
host = 127.0.0.1
port = 9380
api_key = your_ragflow_api_key
default_kb = policy_demo_kb

[QWEN]
api_key = your_qwen_api_key
model = qwen-plus

[WHISPER]
host = 127.0.0.1
port = 9000
api_key = your_whisper_api_key
```

### 5. 初始化数据库

```bash
# 数据库会自动创建，也可以手动初始化
python -c "from src.database.db_manager import DBManager; DBManager().init_database()"
```

### 6. 启动应用

```bash
streamlit run app.py --server.port=8501
```

访问: http://localhost:8501

---

## Docker部署

### 架构

**文件**: [docker/docker-compose.yml](../../docker/docker-compose.yml)

```yaml
version: '3.8'

services:
  # Streamlit应用
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: policy_system_app
    ports:
      - "8501:8501"
    environment:
      - RAGFLOW_HOST=ragflow
      - RAGFLOW_PORT=9380
      - WHISPER_HOST=whisper
      - WHISPER_PORT=9000
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
      - ../config:/app/config
    depends_on:
      ragflow:
        condition: service_healthy
      whisper:
        condition: service_healthy
    networks:
      - policy_network
    restart: unless-stopped

  # RAGFlow服务
  ragflow:
    image: infiniflow/ragflow:latest
    container_name: policy_ragflow
    ports:
      - "9380:9380"
    environment:
      RAGFLOW_HOME: /home/ragflow
    volumes:
      - ragflow_data:/home/ragflow/data
    networks:
      - policy_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9380/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Whisper服务
  whisper:
    image: onerahmet/openai-whisper-asr-webservice:latest
    container_name: policy_whisper
    ports:
      - "9000:9000"
    environment:
      ASR_MODEL: base
    networks:
      - policy_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  ragflow_data:

networks:
  policy_network:
    driver: bridge
```

### 部署步骤

#### 1. 构建镜像

```bash
cd Investopedia

# 构建应用镜像
docker-compose -f docker/docker-compose.yml build
```

#### 2. 启动服务

```bash
# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 查看服务状态
docker-compose -f docker/docker-compose.yml ps

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f app
```

#### 3. 健康检查

```bash
# 检查应用
curl http://localhost:8501

# 检查RAGFlow
curl http://localhost:9380/health

# 检查Whisper
curl http://localhost:9000/health
```

#### 4. 停止服务

```bash
# 停止所有服务
docker-compose -f docker/docker-compose.yml down

# 停止并删除数据卷
docker-compose -f docker/docker-compose.yml down -v
```

---

## 生产环境部署

### 1. 使用反向代理

**Nginx配置示例**:

```nginx
upstream policy_system {
    server localhost:8501;
}

server {
    listen 80;
    server_name policy.example.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name policy.example.com;

    # SSL证书
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 代理配置
    location / {
        proxy_pass http://policy_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持（Streamlit需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 日志
    access_log /var/log/nginx/policy_access.log;
    error_log /var/log/nginx/policy_error.log;
}
```

### 2. 环境变量管理

**使用.env文件**:

```bash
# .env文件（不要提交到Git）
RAGFLOW_API_KEY=prod_ragflow_key_xxx
QWEN_API_KEY=prod_qwen_key_xxx
WHISPER_API_KEY=prod_whisper_key_xxx

DATABASE_PATH=/data/production/policies.db
LOG_LEVEL=INFO
```

**Docker Compose使用.env**:
```yaml
services:
  app:
    env_file:
      - .env
```

### 3. 使用外部数据库（可选）

**PostgreSQL配置**:

```python
# config.ini
[DATABASE]
type = postgresql
host = db.example.com
port = 5432
database = policies
user = policy_user
password = ${DB_PASSWORD}  # 从环境变量读取
```

---

## 配置管理

### 配置优先级

```
环境变量 > config.ini > config.ini.template
```

### 敏感信息处理

**❌ 不安全**:
```ini
[QWEN]
api_key = sk-xxx123456789  # 硬编码API密钥
```

**✅ 安全**:
```ini
[QWEN]
api_key = ${QWEN_API_KEY}  # 从环境变量读取
```

```bash
# 设置环境变量
export QWEN_API_KEY=sk-xxx123456789
```

### 多环境配置

```
config/
├── config.ini.template      # 配置模板
├── config.dev.ini          # 开发环境
├── config.staging.ini      # 预发布环境
└── config.prod.ini         # 生产环境
```

**启动时指定环境**:
```bash
# 开发环境
export ENV=dev
streamlit run app.py

# 生产环境
export ENV=prod
streamlit run app.py
```

---

## 监控和日志

### 日志配置

**文件**: [src/utils/logger.py](../../src/utils/logger.py)

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### 日志分级

```
logs/
├── app.log           # 应用日志
├── error.log         # 错误日志
├── access.log        # 访问日志
└── performance.log   # 性能日志
```

### 日志轮转

**使用logrotate**:

```bash
# /etc/logrotate.d/policy_system
/path/to/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload policy_system
    endscript
}
```

### 监控指标

**关键指标**:

```python
# 系统指标
- CPU使用率
- 内存使用率
- 磁盘空间
- 网络流量

# 应用指标
- 请求QPS
- 响应时间（P50/P95/P99）
- 错误率
- API调用次数

# 业务指标
- 活跃用户数
- 文档上传数
- 图谱节点数
- 问答请求数
```

**使用Prometheus + Grafana**:

```yaml
# docker-compose.yml添加监控
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 故障排查

### 常见问题

#### 1. 应用无法启动

**检查步骤**:
```bash
# 1. 查看日志
docker logs policy_system_app

# 2. 检查端口占用
netstat -tuln | grep 8501

# 3. 检查配置
python -c "from src.config import get_config; print(get_config())"

# 4. 检查依赖
pip list | grep streamlit
```

#### 2. RAGFlow连接失败

**检查步骤**:
```bash
# 1. 检查RAGFlow服务
curl http://localhost:9380/health

# 2. 检查网络连通性
ping ragflow  # 容器名

# 3. 查看RAGFlow日志
docker logs policy_ragflow

# 4. 验证API密钥
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:9380/api/datasets
```

#### 3. 数据库锁定

**解决方案**:
```bash
# 关闭所有连接
pkill -f streamlit

# 删除锁文件
rm data/database/policies.db-journal

# 重启应用
streamlit run app.py
```

#### 4. 内存不足

**检查内存**:
```bash
# 查看内存使用
docker stats policy_system_app

# 增加Docker内存限制
docker-compose -f docker/docker-compose.yml up -d \
  --scale app=1 \
  --memory="4g"
```

---

## 备份和恢复

### 数据备份

**备份脚本**:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据库
cp data/database/policies.db $BACKUP_DIR/

# 备份配置
cp -r config $BACKUP_DIR/

# 备份日志
cp -r logs $BACKUP_DIR/

# 压缩
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "备份完成: $BACKUP_DIR.tar.gz"
```

**定时备份** (crontab):
```bash
# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

### 数据恢复

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

# 解压
tar -xzf $BACKUP_FILE -C /tmp/

# 恢复数据库
cp /tmp/backup/policies.db data/database/

# 恢复配置
cp -r /tmp/backup/config/* config/

# 重启应用
docker-compose -f docker/docker-compose.yml restart app

echo "恢复完成"
```

---

## 最佳实践

### 1. 安全加固

```bash
# 限制文件权限
chmod 600 config/config.ini
chmod 700 data/database/

# 使用非root用户运行
USER=appuser
```

### 2. 资源限制

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 3. 健康检查

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8501"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 4. 自动重启

```yaml
restart: unless-stopped  # 容器异常退出时自动重启
```

### 5. 版本管理

```bash
# 使用Git标签管理版本
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 构建时使用版本号
docker build -t policy-system:v1.0.0 .
```

---

## 相关文档

- [配置详解](../06-CONFIGURATION.md) - 完整配置项说明
- [系统架构](../02-ARCHITECTURE.md) - 了解系统组件
- [故障排查](../08-TROUBLESHOOTING.md) - 更多故障解决方案
- [性能优化](performance.md) - 生产环境性能调优

---

**最后更新**: 2026-02-01  
**维护者**: AI Assistant
