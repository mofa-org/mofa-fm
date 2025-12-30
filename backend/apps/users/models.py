"""
用户模型
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """扩展用户模型"""

    email = models.EmailField('邮箱', unique=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    bio = models.TextField('个人简介', max_length=500, blank=True)

    # 创作者标记
    is_creator = models.BooleanField('创作者', default=False)
    is_verified = models.BooleanField('认证标记', default=False, help_text='官方认证')
    email_verified = models.BooleanField('邮箱已验证', default=False)

    # 统计字段（反范式）
    shows_count = models.IntegerField('节目数', default=0)
    total_plays = models.IntegerField('总播放量', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
        """获取头像URL"""
        if self.avatar:
            return self.avatar.url
        return None


class CreatorVerification(models.Model):
    """创作者验证记录"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='creator_verification',
        verbose_name='用户'
    )

    # 数学题验证
    question = models.CharField('问题', max_length=100, blank=True, null=True)
    answer = models.IntegerField('答案', blank=True, null=True)

    # 验证状态
    is_verified = models.BooleanField('已验证', default=False)
    attempts = models.IntegerField('尝试次数', default=0)

    verified_at = models.DateTimeField('验证时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'creator_verifications'
        verbose_name = '创作者验证'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} - {'已验证' if self.is_verified else '未验证'}"

    def verify(self, user_answer):
        """验证答案"""
        self.attempts += 1
        self.save()

        if int(user_answer) == self.answer:
            self.is_verified = True
            self.verified_at = timezone.now()
            self.save()

            # 更新用户创作者状态
            self.user.is_creator = True
            self.user.save()

            return True
        return False
