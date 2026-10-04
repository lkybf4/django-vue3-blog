import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_backend.settings')
django.setup()

from django.contrib.auth.models import User
from apps.articles.models import Article

user, created = User.objects.get_or_create(username='admin')
user.email = 'admin@example.com'
user.is_superuser = True
user.is_staff = True
user.set_password('admin123')
user.save()
print(f"用户: admin (created={created}, 密码=admin123)")

data = [
    ('Python 装饰器完全指南', '# Python 装饰器\n\n装饰器是 Python 的重要特性。'),
    ('Django ORM 高级查询', '# Django ORM 高级查询\n\n掌握 Q 对象和 F 对象。'),
    ('Vue3 组合式 API', '# Vue3 组合式 API\n\n使用 ref 和 reactive。'),
    ('Redis 缓存实战', '# Redis 缓存实战\n\n用 Redis 缓存文章列表。'),
    ('Docker 部署指南', '# Docker 部署指南\n\n一键启动前后端全栈环境。'),
]

for title, content in data:
    obj, created = Article.objects.get_or_create(
        title=title,
        defaults={'content': content, 'author': user, 'status': 'published'},
    )
    print(f"  {'创建' if created else '已存在'}: {title}")

print(f"\n文章总数: {Article.objects.count()}")