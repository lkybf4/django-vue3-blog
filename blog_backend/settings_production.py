import os
import dj_database_url
from .settings import *

# 1. 基础安全设置
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-build')
ALLOWED_HOSTS = ['*'] # 允许所有域名，省事。部署成功后可改成 Render 分配的域名

# 2. 数据库配置（自动读取 Render 提供的环境变量）
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

# 3. 静态文件配置（Whitenoise 接管）
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# 4. 跨域与 CSRF 配置
CORS_ALLOW_ALL_ORIGINS = True # 简单粗暴允许所有
CORS_ALLOW_CREDENTIALS = True

# 5. 缓存（线上先用本地内存缓存，保证跑通，以后再换 Redis）
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}