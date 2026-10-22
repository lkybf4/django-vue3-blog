from django.core.cache import cache
from django.db.models import Count, Q
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from .models import Article, HAS_POSTGRES_SEARCH
from .permissions import IsAuthorOrStaff
from .cache import (
    article_list_cache_key,
    bump_article_aggregate_cache,
    bump_article_list_cache,
)
from .serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateSerializer
)


class ArticleListView(generics.ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary']
    ordering_fields = ['created_at', 'views']
    ordering = ['-is_top', '-created_at']

    def _mine_requested(self):
        return self.request.query_params.get('mine', '').lower() in ('1', 'true', 'yes')

    def get_queryset(self):
        queryset = super().get_queryset()
        if self._mine_requested():
            # ?mine=1 返回当前用户自己的全部文章（含草稿），供编辑器/个人中心使用
            if not self.request.user.is_authenticated:
                return Article.objects.none()
            queryset = queryset.filter(author=self.request.user)
        else:
            queryset = queryset.filter(status='published')

        queryset = queryset.select_related(
            'author', 'category'
        ).prefetch_related('tags').defer('content').annotate(
            comments_count=Count('comments', distinct=True)
        )

        search_query = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        tag = self.request.query_params.get('tag', None)
        series = self.request.query_params.get('series', None)
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)

        if category:
            queryset = queryset.filter(category__slug=category)
        if tag:
            queryset = queryset.filter(tags__slug=tag)
        if series:
            queryset = queryset.filter(series__slug=series)
        if year:
            queryset = queryset.filter(created_at__year=year)
        if month:
            queryset = queryset.filter(created_at__month=month)

        if HAS_POSTGRES_SEARCH and search_query:
            try:
                from django.db import connection
                from django.contrib.postgres.search import SearchQuery, SearchRank
                if connection.vendor == 'postgresql':
                    search_vector = 'search_vector'
                    query = SearchQuery(search_query)
                    queryset = queryset.annotate(
                        rank=SearchRank(search_vector, query)
                    ).filter(
                        search_vector=query
                    ).order_by('-rank')
            except Exception:
                pass
        return queryset

    def list(self, request, *args, **kwargs):
        # 个人文章列表按用户区分，不做公共缓存
        mine = self._mine_requested()
        cache_key = None
        if not mine:
            cache_key = article_list_cache_key(request.query_params)
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)
        response = super().list(request, *args, **kwargs)
        if cache_key is not None:
            cache.set(cache_key, response.data, 300)
        return response


class ArticleDetailView(generics.RetrieveAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleDetailSerializer

    def get_queryset(self):
        queryset = Article.objects.select_related(
            'author', 'category', 'series'
        ).prefetch_related('tags')
        if self.request.user.is_authenticated:
            # 作者可以看到自己的草稿
            return queryset.filter(Q(status='published') | Q(author=self.request.user))
        return queryset.filter(status='published')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == 'published':
            instance.increase_views()

        # 草稿只有作者可见，不能进公共缓存
        if instance.status != 'published':
            serializer = self.get_serializer(instance)
            data = serializer.data
            data['related_articles'] = self.get_related_articles(instance)
            return Response(data)

        cache_key = f'article_detail:{instance.id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            cached_data['views'] = instance.views
            return Response(cached_data)

        serializer = self.get_serializer(instance)
        data = serializer.data

        related = self.get_related_articles(instance)
        data['related_articles'] = related

        cache.set(cache_key, data, 600)
        return Response(data)

    def get_related_articles(self, article, limit=4):
        related_qs = Article.objects.filter(status='published').exclude(id=article.id)

        if article.category_id:
            related_qs = related_qs.filter(
                Q(category_id=article.category_id) |
                Q(tags__in=article.tags.all())
            ).distinct()
        else:
            related_qs = related_qs.filter(tags__in=article.tags.all()).distinct()

        if related_qs.count() < limit:
            related_qs = Article.objects.filter(
                status='published'
            ).exclude(id=article.id).order_by('-views')

        related = related_qs[:limit]

        return [
            {
                'id': a.id, 'title': a.title, 'slug': a.slug,
                'summary': a.summary, 'views': a.views, 'created_at': a.created_at
            }
            for a in related
        ]


class ArticleCreateView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleCreateSerializer
    permission_classes = [IsAuthenticated]  # 允许 authenticated 用户发布文章

    def perform_create(self, serializer):
        serializer.save()
        bump_article_list_cache()
        bump_article_aggregate_cache()


class ArticleUpdateView(generics.UpdateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleCreateSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrStaff]

    def perform_update(self, serializer):
        article = serializer.save()
        cache.delete(f'article_detail:{article.id}')
        bump_article_list_cache()
        bump_article_aggregate_cache()


class ArticleDeleteView(generics.DestroyAPIView):
    queryset = Article.objects.all()
    permission_classes = [IsAuthenticated, IsAuthorOrStaff]

    def perform_destroy(self, instance):
        instance_id = instance.id
        instance.delete()
        cache.delete(f'article_detail:{instance_id}')
        bump_article_list_cache()
        bump_article_aggregate_cache()
     
