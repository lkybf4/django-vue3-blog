from rest_framework import generics, status,permissions
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache

from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer
from .throttles import CommentRateThrottle
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self,request,view,obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated or not request.user:#未登录和未注册用户无法删除评论
            return False
        return obj.author == request.user#对于非safe方法，只有评论的人是作者才能删评论


class CommentListView(generics.ListAPIView):#评论列表公开
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        article_id = self.kwargs.get('article_id')
        return Comment.objects.filter(
            article_id=article_id,
            is_approved=True,
            parent=None
        ).select_related('author').prefetch_related(
            'replies__author'
        ).order_by('-created_at')


class CommentCreateView(generics.CreateAPIView):#发表或创建评论
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [CommentRateThrottle]

    def perform_create(self, serializer):
        comment = serializer.save()
        cache.delete(f'article_detail:{comment.article.id}')


class CommentDeleteView(generics.DestroyAPIView):#删除评论
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated,IsOwnerOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        article_id = instance.article.id
        self.perform_destroy(instance)
        cache.delete(f'article_detail:{article_id}')
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
