# 个人博客系统

基于 Django 5 + DRF + Vue 3 的前后端分离博客系统。


## 功能

- JWT 登录注册（access + refresh 双 token）
- Markdown 文章发布，渲染后 XSS 过滤
- 楼中楼评论
- 文章列表分页、搜索
- Swagger API 文档

## 技术栈

- 后端：Django 5.x / DRF / SimpleJWT / SQLite
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

（简要列表）

## 项目结构

（目录树）

## 已知问题 / 待办

- [ ] 部署到公网
- [ ] 补充单元测试
- [ ] 图片上传

## License

MIT