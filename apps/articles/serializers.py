import math
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Article, Category, Tag, Series


class EmptyStringToNullImageField(serializers.ImageField):
    """
    自定义 ImageField：把空字符串转成 None
    DRF 原生 ImageField 不接受空字符串，但前端常传 "" 表示"没有图片"
    """
    def to_internal_value(self, data):
        if data == '' or data is None:
            return None
        return super().to_internal_value(data)
class ExternalImageField(serializers.Field):
    """自定义字段，处理外部URL和本地图片的混合情况"""
    def to_representation(self, value):
        if not value:
            return None
        value_str = str(value)
        if value_str.startswith(('http://', 'https://')):
            return value_str
        return value.url if hasattr(value, 'url') else None
    
    def to_internal_value(self, data):
        return data


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class CategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'color', 'order', 'article_count']


class TagSerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'article_count']


class SeriesListSerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)
    cover = ExternalImageField(required=False, allow_null=True)

    class Meta:
        model = Series
        fields = ['id', 'title', 'slug', 'description', 'cover', 'article_count', 'created_at']


class SeriesDetailSerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)
    articles = serializers.SerializerMethodField()
    cover = ExternalImageField(required=False, allow_null=True)

    class Meta:
        model = Series
        fields = ['id', 'title', 'slug', 'description', 'cover', 'article_count', 'articles', 'created_at']

    def get_articles(self, obj):
        articles = obj.articles.filter(status='published').order_by('-created_at')
        return ArticleListSerializer(articles, many=True).data


class ArticleListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    category_slug = serializers.CharField(source='category.slug', read_only=True, default=None)
    tags = TagSerializer(many=True, read_only=True)
    reading_time = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(read_only=True, default=0)
    cover = serializers.CharField(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'summary', 'cover', 'author_name', 'nickname',
            'category_name', 'category_slug', 'tags', 'is_top',
            'views', 'reading_time', 'comments_count', 'created_at', 'updated_at'
        ]

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.username
        return obj.nickname

    def get_reading_time(self, obj):
        word_count = len(getattr(obj, 'content', '') or '')
        minutes = math.ceil(word_count / 500)
        return max(1, minutes)


class ArticleDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    series = SeriesListSerializer(read_only=True)
    cover = serializers.CharField(read_only=True)
    reading_time = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'content_html', 'summary',
            'cover', 'author_name', 'nickname', 'category', 'tags', 'series', 'is_top',
            'views', 'reading_time', 'comments_count', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['content_html', 'views']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.username
        return obj.nickname

    def get_reading_time(self, obj):
        word_count = len(obj.content) if obj.content else 0
        minutes = math.ceil(word_count / 500)
        return max(1, minutes)

    def get_comments_count(self, obj):
        return obj.comments.filter(is_approved=True).count()


class ArticleCreateSerializer(serializers.ModelSerializer):
    cover = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', required=False, allow_null=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, required=False
    )
    series_id = serializers.PrimaryKeyRelatedField(
        queryset=Series.objects.all(), source='series', required=False, allow_null=True
    )

    class Meta:
        model = Article
        fields = [
            'title', 'slug', 'content', 'content_html', 'summary', 'cover',
            'status', 'is_top', 'nickname', 'category_id', 'tag_ids', 'series_id'
        ]
        read_only_fields=['content_html','slug','summary']

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            validated_data['author'] = user
        if not validated_data.get('nickname'):
            validated_data['nickname'] = (
                user.username if user and user.is_authenticated else '匿名用户'
            )
        # 置顶属于运营权限，只有管理员可以设置
        if not (user and user.is_staff):
            validated_data.pop('is_top', None)
        # 草稿/发布二选一，非法值一律按发布处理
        if validated_data.get('status') not in dict(Article.STATUS_CHOICES):
            validated_data['status'] = 'published'
        tags = validated_data.pop('tags', [])
        article = super().create(validated_data)
        if tags:
            article.tags.set(tags)
        return article

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not (user and user.is_staff):
            validated_data.pop('is_top', None)
        if 'status' in validated_data and validated_data['status'] not in dict(Article.STATUS_CHOICES):
            validated_data.pop('status')
        tags = validated_data.pop('tags', None)
        article = super().update(instance, validated_data)
        if tags is not None:
            article.tags.set(tags)
        return article
