"""文章模块的回归测试：覆盖编辑、权限、草稿、置顶、RSS 与归档。"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.articles.models import Article


class ArticleUpdatePermissionTest(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='TestPass123!')
        self.other = User.objects.create_user(username='other', password='TestPass123!')
        self.staff = User.objects.create_user(
            username='staff', password='TestPass123!', is_staff=True
        )
        self.article = Article.objects.create(
            title='原始标题', content='原始内容', author=self.author, status='published'
        )

    def test_author_can_patch_own_article(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(
            f'/api/articles/{self.article.id}/update/',
            {'title': '改后的标题'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, '改后的标题')

    def test_author_can_put_own_article(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.put(
            f'/api/articles/{self.article.id}/update/',
            {'title': 'PUT 标题', 'content': 'PUT 内容'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_update_article(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(
            f'/api/articles/{self.article.id}/update/',
            {'title': '恶意修改'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create_article(self):
        response = self.client.post(
            '/api/articles/create/',
            {'title': '匿名发布', 'content': 'x'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ArticlePublishRulesTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='normal', password='TestPass123!')
        self.staff = User.objects.create_user(
            username='staff', password='TestPass123!', is_staff=True
        )

    def test_normal_user_cannot_pin_article(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/articles/create/',
            {'title': '想置顶', 'content': 'x', 'is_top': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        article = Article.objects.get(title='想置顶')
        self.assertFalse(article.is_top)

    def test_staff_can_pin_article(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(
            '/api/articles/create/',
            {'title': '管理员置顶', 'content': 'x', 'is_top': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        article = Article.objects.get(title='管理员置顶')
        self.assertTrue(article.is_top)

    def test_draft_can_be_created_and_is_private(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/articles/create/',
            {'title': '我的草稿', 'content': 'x', 'status': 'draft'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        draft = Article.objects.get(title='我的草稿')
        self.assertEqual(draft.status, 'draft')

        # 公共列表不包含草稿
        public = self.client.get('/api/articles/')
        titles = [item['title'] for item in public.data['results']]
        self.assertNotIn('我的草稿', titles)

        # 作者自己的列表能看到
        mine = self.client.get('/api/articles/?mine=1')
        mine_titles = [item['title'] for item in mine.data['results']]
        self.assertIn('我的草稿', mine_titles)

        # 作者能打开详情
        detail = self.client.get(f'/api/articles/{draft.id}/')
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_read_draft(self):
        draft = Article.objects.create(
            title='私有草稿', content='x', author=self.user, status='draft'
        )
        response = self.client.get(f'/api/articles/{draft.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ArticlePublicEndpointTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='writer', password='TestPass123!')
        self.article = Article.objects.create(
            title='正常文章', content='内容', author=self.author, status='published'
        )

    def test_rss_feed_available(self):
        response = self.client.get('/api/articles/rss/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b'<rss', response.content.lower())

    def test_archive_month_by_author_available(self):
        created = timezone.localtime(self.article.created_at)
        response = self.client.get(
            f'/api/articles/archive/{created.year}/{created.month}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_archive_month_survives_deleted_author(self):
        created = timezone.localtime(self.article.created_at)
        self.author.delete()
        self.article.refresh_from_db()
        self.assertIsNone(self.article.author)

        response = self.client.get(
            f'/api/articles/archive/{created.year}/{created.month}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['articles'][0]['author'], self.article.nickname)

    def test_rss_survives_deleted_author(self):
        self.author.delete()
        response = self.client.get('/api/articles/rss/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
