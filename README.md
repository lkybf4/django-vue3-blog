# 个人博客系统

基于 Django 5 + DRF + Vue 3 的前后端分离博客系统。

**在线demo**：
## 功能

- JWT 登录注册（access + refresh 双 token）
- Markdown 文章发布，渲染后 XSS 过滤
- 楼中楼评论
- 文章列表分页、搜索
- Swagger API 文档

## 技术栈

- 后端：Django 5.2 / DRF / SimpleJWT / SQLite
- 前端：Vue 3 / Vite / Pinia / Vue Router / Axios
- 文档：drf-spectacular

## 快速开始

### 后端
\`\`\`bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

pip install -r requirements.txt
python manage.py migrate
python seed.py                 # 灌示例数据
python manage.py runserver
\`\`\`

### 前端
\`\`\`bash
cd blog-frontend
npm install
npm run dev
\`\`\`

访问：
- 前端 http://localhost:5173
- 后端 API http://localhost:8000
- API 文档 http://localhost:8000/api/docs/

### 测试账号
- admin / admin123

## API 端点

所有接口以 `/api/` 为前缀，完整文档见 Swagger UI：http://localhost:8000/api/docs/

### 认证 Auth

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| POST | `/api/auth/register/` | 用户注册 | ❌ |
| POST | `/api/auth/token/` | 登录获取 JWT（返回 access + refresh） | ❌ |
| POST | `/api/auth/token/refresh/` | 用 refresh token 换新的 access token | ❌ |
| GET  | `/api/auth/profile/` | 获取当前登录用户信息 | ✅ |
| PUT  | `/api/auth/profile/` | 更新当前用户信息 | ✅ |
| PATCH | `/api/auth/profile/` | 部分更新当前用户信息 | ✅ |

### 文章 Articles

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| GET    | `/api/articles/` | 文章列表，支持分页 `?page=`、搜索 `?search=`、排序 `?ordering=` | ❌ |
| GET    | `/api/articles/{id}/` | 文章详情（含 Markdown 渲染后的 HTML） | ❌ |
| POST   | `/api/articles/create/` | 创建文章 | ❌ |
| PUT    | `/api/articles/{id}/update/` | 更新文章（完整覆盖） | ✅ |
| PATCH  | `/api/articles/{id}/update/` | 更新文章（部分字段） | ✅ |
| DELETE | `/api/articles/{id}/delete/` | 删除文章 | ✅ |
| POST   | `/api/articles/upload-image/` | 上传图片（用于 Markdown 内嵌） | ❌ |

### 评论 Comments

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| GET    | `/api/comments/article/{article_id}/` | 获取某篇文章的评论列表（分页） | ❌ |
| POST   | `/api/comments/create/` | 发表评论（支持 `parent` 字段实现楼中楼） | ✅ |
| DELETE | `/api/comments/{id}/delete/` | 删除评论（仅作者或管理员） | ✅ |

### 站点 Site

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| GET | `/api/site/` | 站点配置（站点名、描述、作者、备案号等） | ❌ |

### 笔记 Notes

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| GET | `/api/notes/` | 笔记列表 | ❌ |

### 系统 System

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health/` | 健康检查 |
| GET | `/readiness/` | 就绪检查 |
| GET | `/admin/` | Django 管理后台 |
| GET | `/api/docs/` | Swagger UI 交互式文档 |
| GET | `/api/schema/` | OpenAPI 3.0 schema |
| GET | `/robots.txt` | 爬虫规则 |
| GET | `/sitemap.xml` | 站点地图 |
## 项目结构

```
django-vue3-blog/
├── apps/                          # Django 业务模块
│   ├── users/                     # 用户认证（注册、JWT 登录）
│   ├── articles/                  # 文章（模型、API、图片上传）
│   ├── comments/                  # 评论（支持嵌套回复）
│   ├── system/                    # 站点配置、健康检查、SEO
│   ├── notes/                     # 笔记模块
│   └── monitoring/                # 监控上报
├── blog_backend/                  # Django 项目配置
│   ├── settings.py                # 开发环境配置
│   ├── settings_production.py     # 生产环境配置
│   ├── urls.py                    # 主路由
│   ├── asgi.py / wsgi.py
│   └── sitemaps.py / seo_views.py
├── blog-frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── api/                   # Axios 封装 + 各模块 API
│   │   ├── views/                 # 页面组件
│   │   ├── components/            # 可复用组件
│   │   ├── router/                # Vue Router 配置
│   │   ├── stores/                # Pinia 状态管理
│   │   ├── composables/           # 组合式函数
│   │   ├── App.vue
│   │   └── main.js
│   ├── vite.config.js             # Vite 配置（含 API 代理）
│   └── package.json
├── scripts/                       # 工具脚本
│   ├── seed.py                    # 灌示例数据
│   └── monitor_agent.py           # 监控客户端
├── manage.py                      # Django 命令入口
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量模板
└── README.md
```

## 已知问题 / 待办

- [ ] 部署到公网
- [ ] 补充单元测试
- [ ] 图片上传

## License

MIT