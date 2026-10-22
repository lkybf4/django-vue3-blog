"""生产环境配置：所有敏感项与部署相关项都从环境变量读取。"""
import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403

DEBUG = False

# ---------------------------------------------------------------------------
# 密钥：必须由环境变量提供。
# 只有在 Docker 构建阶段执行 collectstatic 时才允许使用一次性占位值。
# ---------------------------------------------------------------------------
_is_build = os.environ.get('DJANGO_BUILDING') == '1'

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if _is_build:
        SECRET_KEY = 'build-time-only-insecure-key'
    else:
        raise ImproperlyConfigured('请设置 SECRET_KEY 环境变量')

# ---------------------------------------------------------------------------
# 允许的主机：环境变量（逗号分隔），并自动包含 Render 分配的域名
# ---------------------------------------------------------------------------
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])

# ---------------------------------------------------------------------------
# 数据库：优先 DATABASE_URL；未设置时启动即失败，避免带着错误配置上线
# ---------------------------------------------------------------------------
_database_url = os.environ.get('DATABASE_URL')
if not _database_url:
    if _is_build:
        _database_url = f'sqlite:///{BASE_DIR / "build.sqlite3"}'
    else:
        raise ImproperlyConfigured('请设置 DATABASE_URL 环境变量（PostgreSQL 连接串）')

DATABASES = {
    'default': dj_database_url.parse(
        _database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ---------------------------------------------------------------------------
# 静态文件：WhiteNoise 托管
# ---------------------------------------------------------------------------
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ---------------------------------------------------------------------------
# 跨域：按白名单放开，前端使用 Bearer Token，不需要携带 cookie 凭据
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = False
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

# 反向代理（Render / Nginx 都在前面终止 TLS）
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))

# ---------------------------------------------------------------------------
# 缓存：配置了 REDIS_URL 就用 Redis，否则退回进程内缓存（单实例可用）
# ---------------------------------------------------------------------------
_redis_url = os.environ.get('REDIS_URL')
if _redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_url,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'blog-production',
        }
    }
