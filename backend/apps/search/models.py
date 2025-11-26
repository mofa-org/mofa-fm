"""
搜索相关模型
"""
from django.db import models
from django.conf import settings


class SearchHistory(models.Model):
    """搜索历史记录"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='search_histories',
        verbose_name='用户',
        null=True,
        blank=True
    )
    query = models.CharField('搜索关键词', max_length=200)
    session_key = models.CharField('会话标识', max_length=100, null=True, blank=True, help_text='未登录用户使用')
    results_count = models.IntegerField('结果数量', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'search_history'
        verbose_name = '搜索历史'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_key', '-created_at']),
            models.Index(fields=['query']),
        ]

    def __str__(self):
        return f"{self.user or self.session_key} - {self.query}"


class PopularSearch(models.Model):
    """热门搜索统计"""
    query = models.CharField('搜索关键词', max_length=200, unique=True)
    search_count = models.IntegerField('搜索次数', default=1)
    last_searched_at = models.DateTimeField('最后搜索时间', auto_now=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'popular_search'
        verbose_name = '热门搜索'
        verbose_name_plural = verbose_name
        ordering = ['-search_count', '-last_searched_at']
        indexes = [
            models.Index(fields=['-search_count', '-last_searched_at']),
        ]

    def __str__(self):
        return f"{self.query} ({self.search_count}次)"
