"""文章相关缓存的键与失效策略。

统一用「版本号」做失效：写操作自增版本，旧 key 自然不再被读取。
这样不依赖 cache.delete_pattern（LocMemCache 没有该方法），也不会误清空
限流计数等其他缓存。
"""
from django.core.cache import cache

ARTICLE_LIST_VERSION_KEY = 'article_list_version'
ARTICLE_ARCHIVE_VERSION_KEY = 'article_archive_version'
ARTICLE_STATISTICS_VERSION_KEY = 'article_statistics_version'


def _bump(key):
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, None)


def bump_article_list_cache():
    """文章发布/编辑/删除、作者信息变化时调用。"""
    _bump(ARTICLE_LIST_VERSION_KEY)


def bump_article_aggregate_cache():
    """归档与统计依赖文章集合和作者名，用户注销后也需要失效。"""
    _bump(ARTICLE_ARCHIVE_VERSION_KEY)
    _bump(ARTICLE_STATISTICS_VERSION_KEY)


def article_list_cache_key(query_params):
    # 使用 urlencode 把 ?page=1&search=xxx 变成安全的字符串
    safe_params = query_params.urlencode() 
    return f"article_list:{safe_params}"


def article_archive_cache_key(name):
    version = cache.get(ARTICLE_ARCHIVE_VERSION_KEY, 0)
    return f'{name}:v{version}'


def article_statistics_cache_key():
    version = cache.get(ARTICLE_STATISTICS_VERSION_KEY, 0)
    return f'article_statistics:v{version}'
