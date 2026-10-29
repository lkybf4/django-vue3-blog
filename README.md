# 文栈 Wenstack · 技术内容发布平台

[![Tests](https://github.com/lkybf4/django-vue3-blog/actions/workflows/test.yml/badge.svg)](https://github.com/lkybf4/django-vue3-blog/actions/workflows/test.yml)

文栈是一个面向技术作者的内容发布平台：支持文章与专栏、分类标签、嵌套评论、全文搜索、归档统计与多作者权限控制。后端用 Django REST Framework 提供 API，前端用 Vue 3 + Vite 单独部署，两者通过 JWT 认证通信。

## 目录

- [技术栈](#技术栈)
- [功能一览](#功能一览)
- [快速开始](#快速开始)
- [API 一览](#api-一览)
- [测试与 CI](#测试与-ci)
- [技术设计说明](#技术设计说明)
- [项目结构](#项目结构)
- [已完成与后续计划](#已完成与后续计划)

## 技术栈

| 层次 | 选型 |
|------|------|
| 后端 | Python 3.12 · Django 6.1 · Django REST Framework 3.18 |
| 认证 | SimpleJWT（access 30 分钟 / refresh 7 天，轮换 + 黑名单） |
| 数据处理 | Markdown + bleach（XSS 白名单过滤）· Pillow（图片上传） |
| 存储 | SQLite（开发）/ PostgreSQL（生产）· Redis 缓存（可选，未配置时用进程内缓存） |
| 前端 | Vue 3（组合式 API）· Vite 5 · Vue Router 4 · Pinia 2 · Axios |
| 文档 | drf-spectacular（Swagger UI） |
| 质量 | Django TestCase / APITestCase · GitHub Actions |
| 部署 | Dockerfile + Gunicorn + WhiteNoise · Docker Compose（本地 PostgreSQL + Redis + 前后端） |

可选扩展（不装也能跑）：Elasticsearch 全文搜索（不可用时自动降级为数据库查询）、Celery 定时任务、Channels WebSocket。

## 功能一览

### 已在本地验证可用

- **认证**：注册、登录、Token 刷新、当前用户资料读写
- **文章**：发布、列表（分页 / 关键词搜索 / 排序 / 按分类·标签·专题筛选）、详情（含渲染后的 HTML 与相关文章推荐）、删除
- **Markdown 渲染**：服务端渲染并落库到 `content_html`，用 bleach 白名单过滤标签与属性（单元测试覆盖 `<script>` 注入用例）
- **评论**：二级"楼中楼"评论的列表与发表，仅评论作者本人可删除
- **内容组织**：分类 / 标签 / 专题、按年月归档与站点统计
- **SEO**：`sitemap.xml`、`robots.txt`、RSS 订阅
- **其他模块**：站点配置、友情链接、个人笔记
- **站点监控**：`scripts/monitor_agent.py` 定时上报服务器指标，后台与前端可视化展示
- **工程化**：分级接口限流、对象级权限、55 个自动化测试、GitHub Actions CI、Gunicorn + WhiteNoise 部署配置

### 已实现但需要额外依赖才能启用

| 功能 | 状态说明 |
|------|----------|
| Elasticsearch 全文搜索 | 代码完成，`USE_ELASTICSEARCH=true` 时启用；未启用或 ES 不可用时自动降级为数据库查询 |
| WebSocket 实时评论 | 消费者与前端组合式函数已完成，需安装 `channels` 并放开 `INSTALLED_APPS` / `ASGI_APPLICATION` 才会生效 |
| 第三方登录 | GitHub / 微信 的 OAuth 客户端代码已完成，路由挂载与联调尚未完成 |
| Celery 定时任务 | 任务函数已完成（统计、周报、临时文件清理），需运行 broker 与 worker |

> 上面这几项在默认配置下**不会生效**，不影响主流程运行。

## 快速开始

### 后端

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python seed.py            # 测试
python manage.py runserver
```

> 开发环境默认使用 SQLite + 进程内缓存，开箱即用；生产环境变量见下方「部署配置」。

### 前端

```bash
cd blog-frontend
npm install
npm run dev
```

Vite 已配置 `/api`、`/media`、`/sitemap.xml`、`/robots.txt`、`/ws` 的代理，前端无需额外配置跨域。

### 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端页面 |
| http://localhost:8000 | 后端 API |
| http://localhost:8000/api/docs/ | Swagger 交互式文档 |
| http://localhost:8000/admin/ | Django 管理后台 |

### 演示账号

执行 `python seed.py` 后可用：`admin` / `admin123`（本地演示用，请勿用于任何公开环境）。

### 部署配置（生产）

`DJANGO_SETTINGS_MODULE=blog_backend.settings_production` 时，以下环境变量生效：

| 变量 | 必填 | 说明 |
|------|:----:|------|
| `SECRET_KEY` | ✅ | Django 密钥，未设置时启动直接报错（不会使用默认值） |
| `DATABASE_URL` | ✅ | PostgreSQL 连接串，如 `postgresql://user:pass@host:5432/db` |
| `DJANGO_ALLOWED_HOSTS` | ✅ | 允许的域名，逗号分隔；Render 会自动追加 `RENDER_EXTERNAL_HOSTNAME` |
| `CORS_ALLOWED_ORIGINS` | ✅ | 允许的前端地址，逗号分隔且带协议 |
| `REDIS_URL` | ❌ | 配置后启用 Redis 缓存，否则退回进程内缓存 |
| `USE_ELASTICSEARCH` | ❌ | 是否启用 ES 搜索 |

## API 一览

所有接口以 `/api/` 为前缀，完整且可在线调试的版本见 Swagger UI：http://localhost:8000/api/docs/

### 认证 `/api/auth/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| POST | `/auth/register/` | 用户注册 | 否 |
| POST | `/auth/token/` | 登录，返回 access + refresh | 否 |
| POST | `/auth/token/refresh/` | 用 refresh 换新的 access（同时轮换 refresh） | 否 |
| GET / PUT / PATCH | `/auth/profile/` | 读取 / 更新当前用户资料 | 是 |
| GET | `/auth/users/` | 用户列表 | 是 |

### 文章 `/api/articles/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| GET | `/articles/` | 列表，支持 `?page=` `?search=` `?ordering=` `?category=` `?tag=` `?series=` `?year=` `?month=`；登录后 `?mine=1` 返回自己的文章（含草稿） | 否 |
| GET | `/articles/{id}/` | 详情（含渲染后 HTML、相关文章；作者可查看自己的草稿） | 否 |
| POST | `/articles/create/` | 发布文章或存草稿（`status=draft`）；`is_top` 仅管理员可设置 | 是 |
| PUT / PATCH | `/articles/{id}/update/` | 编辑文章 | 是（仅作者 / 管理员） |
| DELETE | `/articles/{id}/delete/` | 删除文章 | 是（仅作者 / 管理员） |
| POST | `/articles/upload-image/` | 上传 Markdown 内嵌图片 | 是 |
| GET | `/articles/search/?q=` | 全文搜索（Elasticsearch 优先，异常时自动降级） | 否 |
| GET | `/articles/categories/` `/tags/` `/series/` `/series/{slug}/` | 分类 / 标签 / 专题 | 否 |
| GET | `/articles/categories/{slug}/articles/` `/tags/{slug}/articles/` | 按分类 / 标签取文章 | 否 |
| GET | `/articles/archive/` `/archive/{year}/` `/archive/{year}/{month}/` `/statistics/` | 归档与统计 | 否 |
| GET | `/articles/rss/` | RSS 订阅 | 否 |

### 评论 `/api/comments/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| GET | `/comments/article/{article_id}/` | 某篇文章的评论（含回复） | 否 |
| POST | `/comments/create/` | 发表评论，带 `parent` 即为回复 | 是 |
| DELETE | `/comments/{id}/delete/` | 删除评论 | 是（仅评论作者本人） |

### 站点 / 笔记 / 监控 / 系统

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:----:|
| GET | `/api/site/` `/api/site/friend-links/` | 站点配置、友情链接 | 否 |
| GET | `/api/notes/` `/api/notes/{id}/` | 笔记列表 / 详情（私有笔记仅作者可见） | 否 |
| POST | `/api/monitoring/report/` | 服务器指标上报（需上报 token） | Token |
| GET | `/api/monitoring/servers/` | 监控服务器列表与最新指标 | 是（仅管理员） |
| GET | `/health/` `/readiness/` | 健康检查 / 就绪检查（含数据库连通性） | 否 |
| GET | `/api/schema/` `/api/docs/` | OpenAPI schema / Swagger UI | 否 |
| GET | `/sitemap.xml` `/robots.txt` | SEO | 否 |

## 测试与 CI

```bash
# 全部测试
python manage.py test apps -v 2

# 只跑文章模块
python manage.py test apps.articles -v 2
```

当前共 55 个用例，覆盖：文章模型（slug 生成与唯一性、Markdown 渲染、XSS 过滤、摘要截取、匿名作者、默认状态）、文章 API（发布 / 编辑 / 删除权限、草稿可见性、置顶权限、RSS、归档、缓存一致性）、评论（模型、嵌套回复、审核状态、删除权限、跨文章回复校验）、用户（模型、注册登录、密码强度、邮箱唯一性）、监控接口权限。

CI 配置见 `.github/workflows/test.yml`，推送或 PR 到 `main` 时自动执行。

## 技术设计说明

### 1. JWT 双 Token 与前端无感刷新

后端 access token 30 分钟、refresh token 7 天，开启轮换并加入黑名单（`ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`），避免 refresh token 被反复使用。

前端在 Axios 响应拦截器里统一处理 401：用 refresh 换到新 access 后**重放原请求**。关键点是并发场景——页面同时发起多个请求时，只让第一个触发刷新，其余请求挂在队列里，等新 token 到手后统一重放，避免"一次刷新引发 N 次刷新"把 token 打废。同时标记 `_retry` 防止同一请求无限重试。

### 2. 对象级权限与作者字段的取舍

列表与详情对已发布内容开放，写操作叠加对象级校验 `IsAuthorOrStaff`——只有作者本人或管理员能改删文章；评论删除权限更严，仅评论作者本人可删。

文章与评论的 `author` 外键用 `SET_NULL` 而非级联删除：用户注销后内容仍保留，展示名回退到 `nickname` 字段。这也意味着所有读取作者名的地方都必须处理 `author` 为空的情况。

### 3. 分级限流

登录、评论、上传、匿名突发流量各自使用独立的 throttle scope，而不是全局一刀切；计数落在缓存里，便于多进程 / 多实例共享。

### 4. 全文搜索的降级设计

搜索优先走 Elasticsearch（多字段加权、模糊匹配），但 ES 被设计成可选依赖：未配置、连接失败或索引未建立时，自动降级为数据库查询，接口契约保持不变，只通过返回体里的 `engine` 字段（`elasticsearch` / `database`）暴露实际走的是哪条链路。

### 5. 缓存策略

文章列表按查询参数分片缓存 5 分钟，详情缓存 10 分钟（命中时单独回写实时阅读量），归档与统计缓存 30 分钟至 1 小时。

失效策略用「版本号」而不是 `delete_pattern`：列表、归档、统计各有一个版本键，写操作（发布 / 编辑 / 删除 / 评论 / 用户注销）自增版本后旧键自然失效。这样既不依赖具体缓存后端的批量删除能力，也不会像 `cache.clear()` 那样把限流计数一起清掉。配置了 `REDIS_URL` 用 Redis，否则用进程内缓存。

### 6. 阅读量原子自增与 Markdown 安全

阅读量用 `F('views') + 1` 在数据库侧原子自增，避免并发读改写导致的丢失更新。

Markdown 在服务端渲染后统一经 bleach 白名单过滤标签与属性，再把结果落库到 `content_html`；前端直接用 `v-html` 展示这份已净化的 HTML，不在客户端二次解析 Markdown，减少 XSS 面。

## 项目结构

```
.
├── apps/
│   ├── users/          # 认证、用户资料、OAuth 客户端代码
│   ├── articles/       # 文章、分类、标签、专题、归档、搜索、图片上传
│   ├── comments/       # 评论（嵌套）、WebSocket 消费者
│   ├── notes/          # 个人笔记
│   ├── system/         # 站点配置、友情链接、健康检查、SEO
│   └── monitoring/     # 服务器指标上报与展示
├── blog_backend/
│   ├── settings.py             # 开发环境配置
│   ├── settings_production.py  # 生产环境配置（环境变量驱动）
│   ├── urls.py / asgi.py / wsgi.py
│   └── sitemaps.py / seo_views.py
├── blog-frontend/
│   └── src/
│       ├── api/          # Axios 实例（Token 注入 + 401 刷新重放）与各模块接口
│       ├── views/        # 页面
│       ├── components/   # 可复用组件
│       ├── composables/  # useCommentWebSocket / useSeo 等
│       ├── stores/       # Pinia（认证、主题）
│       └── router/
├── scripts/
│   ├── monitor_agent.py  # 服务器监控采集上报脚本
│   └── seed.py           # 演示数据
├── manage.py · requirements.txt · .env.example
└── Dockerfile · docker-compose.yml · DEPLOYMENT.md
```

## 已完成与后续计划

### 已完成的加固

- [x] 修复文章编辑接口（`PUT/PATCH`）的缓存清理异常
- [x] 收紧发布权限：仅登录用户可发布，`is_top` 仅管理员可设置，支持草稿
- [x] 注册接入 Django 密码强度校验与邮箱唯一性校验
- [x] 监控指标接口限制为仅管理员可读
- [x] 修复作者注销后 RSS / 按年月归档的空值崩溃
- [x] 修复归档接口冷缓存返回对象、热缓存返回数组的结构不一致
- [x] 缓存失效改为版本号机制，不再用 `cache.clear()` 误清限流计数
- [x] 依赖清单与 `pyproject.toml` 对齐，补齐 WhiteNoise / Gunicorn
- [x] 生产配置不再内置默认 `SECRET_KEY`，`ALLOWED_HOSTS` / CORS 改为环境变量驱动
- [x] 测试从 34 个增加到 55 个，CI 覆盖全部 app

### 后续计划

- [ ] 启用 WebSocket 实时评论（安装并配置 `channels`）
- [ ] 补齐第三方登录路由与联调（GitHub / 微信客户端代码已就绪）
- [ ] 补全 Celery 邮件模板（`templates/emails/*.html` 目前不存在）
- [ ] 为部分视图补充 Swagger `serializer_class` 注解
- [ ] 媒体文件迁移到对象存储（当前演示环境由 Django 提供 `media`）
- [ ] 增加覆盖率统计与前端单元测试

## License

MIT
