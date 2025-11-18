"""
互动模型
"""
from django.db import models
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey


class Follow(models.Model):
    """关注播客节目"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='用户'
    )
    show = models.ForeignKey(
        'podcasts.Show',
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='播客节目'
    )
    created_at = models.DateTimeField('关注时间', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'follows'
        unique_together = [['user', 'show']]
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = '关注'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 关注 {self.show.title}"


class Like(models.Model):
    """点赞单集"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='用户'
    )
    episode = models.ForeignKey(
        'podcasts.Episode',
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='单集'
    )
    created_at = models.DateTimeField('点赞时间', auto_now_add=True)

    class Meta:
        db_table = 'likes'
        unique_together = [['user', 'episode']]
        verbose_name = '点赞'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 点赞 {self.episode.title}"


class PlayHistory(models.Model):
    """播放历史和进度"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='play_history',
        verbose_name='用户'
    )
    episode = models.ForeignKey(
        'podcasts.Episode',
        on_delete=models.CASCADE,
        related_name='plays',
        verbose_name='单集'
    )

    position = models.IntegerField('播放位置', default=0, help_text='当前播放位置（秒）')
    completed = models.BooleanField('已完成', default=False)

    last_played_at = models.DateTimeField('最后播放时间', auto_now=True, db_index=True)
    created_at = models.DateTimeField('首次播放时间', auto_now_add=True)

    class Meta:
        db_table = 'play_history'
        unique_together = [['user', 'episode']]
        indexes = [
            models.Index(fields=['user', '-last_played_at']),
        ]
        verbose_name = '播放历史'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 播放 {self.episode.title}"


class Comment(MPTTModel):
    """评论（支持嵌套）"""

    episode = models.ForeignKey(
        'podcasts.Episode',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='单集'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='用户'
    )

    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父评论'
    )

    text = models.TextField('内容', max_length=2000)

    # 时间戳评论（可选，用于标记音频中的时刻）
    timestamp = models.IntegerField(
        '时间戳',
        null=True,
        blank=True,
        help_text='音频位置（秒）'
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'comments'
        indexes = [
            models.Index(fields=['episode', '-created_at']),
        ]
        verbose_name = '评论'
        verbose_name_plural = verbose_name

    class MPTTMeta:
        order_insertion_by = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"
