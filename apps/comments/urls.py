from django.urls import path
from .views import CommentListView, CommentCreateView, CommentDeleteView

urlpatterns = [
    path('article/<int:article_id>/', CommentListView.as_view(), name='comment-list'),
    path('create/', CommentCreateView.as_view(), name='comment-create'),
    path('<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),
]
