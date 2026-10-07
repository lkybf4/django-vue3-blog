"""
Article 模型的单元测试
"""
from django.test import TestCase
from django.contrib.auth.models import User
from apps.articles.models import Article


class ArticleModelTest(TestCase):
    """测试 Article 模型的各种行为"""

    @classmethod
    def setUpTestData(cls):
        """
        setUpTestData: 整个测试类执行前运行一次
        （比每个方法都跑一遍 setUp 快很多）
        这里创建一个测试用户，后面所有方法都能用
        """
        cls.user = User.objects.create_user(
            username='tester',
            password='TestPass123!'
        )

    # ============================
    # 测试 1：slug 自动生成
    # ============================
    def test_slug_auto_generated(self):
        """创建文章时，应该自动生成 slug"""
        article = Article.objects.create(
            title='Python Decorator Guide',
            content='# Hello World',
            author=self.user,
        )
        # assertIsNotNone: 断言不是 None
        self.assertIsNotNone(article.slug)
        # assertNotEqual: 断言不等于空字符串
        self.assertNotEqual(article.slug, '')

    # ============================
    # 测试 2：slug 唯一性
    # ============================
    def test_slug_uniqueness(self):
        """两篇相同标题的文章，slug 不能冲突"""
        article1 = Article.objects.create(
            title='Same Title', content='x', author=self.user
        )
        article2 = Article.objects.create(
            title='Same Title', content='y', author=self.user
        )
        # 如果 slug 生成逻辑没加随机后缀，这里会失败
        self.assertNotEqual(article1.slug, article2.slug)

    # ============================
    # 测试 3：XSS 防护
    # ============================
    def test_xss_script_filtered(self):
        """Markdown 渲染后，<script> 标签应该被过滤掉"""
        article = Article.objects.create(
            title='XSS Test',
            content='Hello <script>alert("xss")</script> World',
            author=self.user,
        )
        # content_html 是渲染后的 HTML
        # 断言里没有 script 标签（bleach 应该过滤掉了）
        self.assertNotIn('<script>', article.content_html)

    # ============================
    # 测试 4：summary 自动生成
    # ============================
    def test_summary_auto_generated(self):
        """内容较长时，summary 应该被自动截取"""
        long_content = '# 标题\n\n' + 'A' * 500
        article = Article.objects.create(
            title='Long Article',
            content=long_content,
            author=self.user,
        )
        # 断言 summary 非空，且长度不超过 200（具体看你代码里的限制）
        self.assertTrue(len(article.summary) > 0)
        self.assertTrue(len(article.summary) <= 200)

    # ============================
    # 测试 5：__str__ 方法
    # ============================
    def test_str_returns_title(self):
        """str(article) 应该返回文章标题"""
        article = Article.objects.create(
            title='My Post', content='x', author=self.user
        )
        self.assertEqual(str(article), 'My Post')

    # ============================
    # 测试 6：默认状态是草稿
    # ============================
    def test_default_status_is_draft(self):
        """新建文章默认状态应该是 draft"""
        article = Article.objects.create(
            title='Test', content='x', author=self.user
        )
        # 你的模型里 status default='draft'
        self.assertEqual(article.status, 'draft')

    # ============================
    # 测试 7：阅读量初始为 0
    # ============================
    def test_views_initial_zero(self):
        """新文章阅读量应该初始为 0"""
        article = Article.objects.create(
            title='Test', content='x', author=self.user
        )
        self.assertEqual(article.views, 0)

    # ============================
    # 测试 8：Markdown 渲染成 HTML
    # ============================
    def test_markdown_rendered_to_html(self):
        """Markdown 内容应该被渲染成 HTML"""
        article = Article.objects.create(
            title='Markdown Test',
            content='# Heading\n\n**bold text**',
            author=self.user,
        )
        # 断言 content_html 里有 <h1> 和 <strong>
        self.assertIn('<h1', article.content_html)
        self.assertIn('<strong>', article.content_html)

    # ============================
    # 测试 9：匿名作者
    # ============================
    def test_anonymous_author_allowed(self):
        """author 可以为空（匿名发布）"""
        article = Article.objects.create(
            title='Anonymous Post',
            content='x',
            author=None,  # 显式传 None
        )
        self.assertIsNone(article.author)

    # ============================
    # 测试 10：昵称默认值
    # ============================
    def test_nickname_default_value(self):
        """不传昵称时，默认是 '匿名用户'"""
        article = Article.objects.create(
            title='Test', content='x', author=self.user
        )
        self.assertEqual(article.nickname, '匿名用户')


class ArticleAPITest(TestCase):
    """测试文章 API 接口"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tester', password='TestPass123!'
        )
        cls.article = Article.objects.create(
            title='API Test',
            content='# Content',
            author=cls.user,
            status='published',
        )

    def test_article_list_api_returns_200(self):
        """GET /api/articles/ 应该返回 200 和分页结构"""
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 断言返回的数据里有分页字段
        self.assertIn('count', data)
        self.assertIn('results', data)

    def test_article_detail_api_returns_200(self):
        """GET /api/articles/{id}/ 应该返回 200"""
        response = self.client.get(f'/api/articles/{self.article.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'API Test')