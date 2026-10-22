from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

from apps.articles.cache import bump_article_aggregate_cache, bump_article_list_cache

from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(pre_delete, sender=User)
def collect_user_article_ids(sender, instance, **kwargs):
    """删除用户前先记下其文章 id（删除后 author 会被置空，查不到了）。"""
    instance._article_ids_for_cache = list(
        instance.articles.values_list('id', flat=True)
    )


@receiver(post_delete, sender=User)
def handle_user_deleted(sender, instance, **kwargs):
    """用户注销后文章会变成 author=None，作者名展示随之变化，需要让相关缓存失效。"""
    for article_id in getattr(instance, '_article_ids_for_cache', []):
        cache.delete(f'article_detail:{article_id}')
    bump_article_list_cache()
    bump_article_aggregate_cache()
