# 博客系统部署指南

## 📋 目录

- [本地开发环境](#本地开发环境)
- [Docker 部署](#docker-部署)
- [生产环境部署](#生产环境部署)
- [环境变量配置](#环境变量配置)

---

## 本地开发环境

### 1. 后端启动

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

后端运行在: http://localhost:8000

### 2. 前端启动

```bash
# 进入前端目录
cd blog-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在: http://localhost:5173

### 3. API 文档

访问 Swagger UI: http://localhost:8000/api/docs/

---

## Docker 部署

### 一键启动（推荐）

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，设置实际的值

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 服务说明

- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Django Backend**: localhost:8000
- **Vue Frontend**: localhost:5173

### 常用命令

```bash
# 重启后端
docker-compose restart backend

# 查看后端日志
docker-compose logs backend

# 进入后端容器
docker-compose exec backend bash

# 执行 Django 命令
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# 清理并重新构建
docker-compose down -v
docker-compose up --build -d
```

---

## 生产环境部署

### 1. 服务器准备

```bash
# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 项目部署

```bash
# 克隆项目
git clone <your-repo-url>
cd blog-project

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 启动服务
docker-compose -f docker-compose.yml up -d

# 设置开机自启
docker-compose up -d
sudo systemctl enable docker
```

### 3. Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 前端
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态文件
    location /static/ {
        alias /path/to/staticfiles/;
    }

    # Media 文件
    location /media/ {
        alias /path/to/media/;
    }
}
```

### 4. HTTPS 配置（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo crontab -e
# 添加: 0 0 1 * * certbot renew --quiet
```

---

## 环境变量配置

### 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DJANGO_SECRET_KEY` | Django 密钥 | 随机字符串 |
| `DB_NAME` | 数据库名称 | blog_db |
| `DB_USER` | 数据库用户 | blog_user |
| `DB_PASSWORD` | 数据库密码 | 强密码 |
| `DB_HOST` | 数据库主机 | localhost / db |
| `REDIS_URL` | Redis 连接 URL | redis://redis:6379/1 |
| `DEBUG` | 调试模式 | True / False |
| `ALLOWED_HOSTS` | 允许的主机 | localhost,yourdomain.com |

### 生成安全的 SECRET_KEY

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

或使用命令行：

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 备份与恢复

### 数据库备份

```bash
# PostgreSQL 备份
docker-compose exec db pg_dump -U blog_user blog_db > backup_$(date +%Y%m%d).sql

# 恢复
docker-compose exec -T db psql -U blog_user blog_db < backup_20240101.sql
```

### Media 文件备份

```bash
# 备份
tar -czf media_backup.tar.gz media/

# 恢复
tar -xzf media_backup.tar.gz
```

---

## 性能优化

### 1. Gunicorn（生产环境 WSGI 服务器）

修改 `docker-compose.yml` 中的 backend 命令：

```yaml
command: >
  sh -c "python manage.py migrate &&
         gunicorn blog_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4"
```

### 2. Nginx 静态文件服务

在 Nginx 配置中添加：

```nginx
location /static/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 3. Redis 缓存优化

确保 Redis 正常运行，监控缓存命中率。

---

## 故障排查

### 常见问题

1. **数据库连接失败**
   ```bash
   docker-compose logs db
   docker-compose restart db
   ```

2. **Redis 连接失败**
   ```bash
   docker-compose logs redis
   docker-compose restart redis
   ```

3. **端口冲突**
   修改 `docker-compose.yml` 中的端口映射

4. **权限问题**
   ```bash
   sudo chown -R $USER:$USER .
   ```

### 查看日志

```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs backend
docker-compose logs frontend
```

---

## 监控与维护

### 健康检查

```bash
# 检查服务状态
docker-compose ps

# 检查资源使用
docker stats
```

### 定期维护

```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的卷
docker volume prune -f

# 更新依赖
docker-compose pull
docker-compose up -d
```

---

## 安全建议

1. ✅ 使用强密码
2. ✅ 启用 HTTPS
3. ✅ 定期更新依赖
4. ✅ 配置防火墙
5. ✅ 限制数据库访问
6. ✅ 启用 CSRF 保护
7. ✅ 使用环境变量管理敏感信息
8. ✅ 定期备份数据

---

## 技术支持

如有问题，请查看：
- Django 文档: https://docs.djangoproject.com/
- Vue.js 文档: https://vuejs.org/
- Docker 文档: https://docs.docker.com/
