"""
播客模型
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from slugify import slugify as awesome_slugify


class Category(models.Model):
    """播客分类"""

    name = models.CharField('名称', max_length=100, unique=True)
    slug = models.SlugField('URL标识', unique=True)
    description = models.TextField('描述', blank=True)
    icon = models.CharField('图标', max_length=50, blank=True, help_text='Element Plus 图标名')
    color = models.CharField('颜色', max_length=7, default='#ff513b', help_text='马卡龙配色')
    order = models.IntegerField('排序', default=0)

    class Meta:
        db_table = 'categories'
        ordering = ['order', 'name']
        verbose_name = '分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """标签"""

    name = models.CharField('名称', max_length=50, unique=True)
    slug = models.SlugField('URL标识', unique=True)

    class Meta:
        db_table = 'tags'
        ordering = ['name']
        verbose_name = '标签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = awesome_slugify(self.name)
        super().save(*args, **kwargs)


class Show(models.Model):
    """播客节目/音乐专辑"""

    CONTENT_TYPE_CHOICES = [
        ('podcast', '播客'),
        ('music', '音乐'),
    ]

    title = models.CharField('标题', max_length=255, db_index=True)
    slug = models.SlugField('URL标识', unique=True, max_length=255)
    description = models.TextField('描述')
    cover = models.ImageField('封面', upload_to='covers/%Y/%m/')
    content_type = models.CharField('内容类型', max_length=20, choices=CONTENT_TYPE_CHOICES, default='podcast', db_index=True)

    # 创作者
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shows',
        verbose_name='创作者'
    )

    # 分类和标签
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shows',
        verbose_name='分类'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='shows', verbose_name='标签')

    # 状态
    is_active = models.BooleanField('激活', default=True)
    is_featured = models.BooleanField('精选', default=False)

    # 统计（反范式）
    episodes_count = models.IntegerField('单集数', default=0)
    followers_count = models.IntegerField('关注数', default=0)
    total_plays = models.IntegerField('总播放', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'shows'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-total_plays']),
            models.Index(fields=['is_featured', '-followers_count']),
        ]
        verbose_name = '播客节目'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = awesome_slugify(self.title)
        super().save(*args, **kwargs)


class Episode(models.Model):
    """播客单集/音乐单曲"""

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('processing', '处理中'),
        ('published', '已发布'),
        ('failed', '处理失败'),
    ]

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name='episodes',
        verbose_name='播客节目'
    )
    title = models.CharField('标题', max_length=255, db_index=True)
    slug = models.SlugField('URL标识', max_length=255)
    description = models.TextField('描述')
    cover = models.ImageField('封面', upload_to='episode_covers/%Y/%m/', blank=True, null=True)

    # 音频文件（统一MP3）
    audio_file = models.FileField('音频文件', upload_to='episodes/%Y/%m/')
    duration = models.IntegerField('时长', default=0, help_text='秒数')
    file_size = models.BigIntegerField('文件大小', default=0, help_text='字节')

    # 播客元数据
    episode_number = models.IntegerField('集数', null=True, blank=True)
    season_number = models.IntegerField('季数', null=True, blank=True)

    # 音乐元数据（可选，仅用于音乐类型）
    artist = models.CharField('艺术家', max_length=255, blank=True, null=True)
    genre = models.CharField('流派', max_length=100, blank=True, null=True, help_text='如：流行、摇滚、古典等')
    album_name = models.CharField('专辑名', max_length=255, blank=True, null=True)
    release_date = models.DateField('发行日期', blank=True, null=True)

    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')

    # 统计
    play_count = models.IntegerField('播放次数', default=0)
    like_count = models.IntegerField('点赞数', default=0)
    comment_count = models.IntegerField('评论数', default=0)

    published_at = models.DateTimeField('发布时间', null=True, blank=True, db_index=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'episodes'
        unique_together = [['show', 'slug']]
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['show', '-published_at']),
            models.Index(fields=['status', '-published_at']),
        ]
        verbose_name = '播客单集'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.show.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = awesome_slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def audio_url(self):
        """获取音频URL"""
        if self.audio_file:
            return self.audio_file.url
        return None

    @property
    def cover_url(self):
        """获取封面URL（如果没有则使用节目封面）"""
        if self.cover:
            return self.cover.url
        return self.show.cover.url if self.show.cover else None


class ScriptSession(models.Model):
    """AI脚本创作会话 - 用户与AI对话生成播客脚本"""

    STATUS_CHOICES = [
        ('active', '进行中'),
        ('completed', '已完成'),
        ('archived', '已归档'),
    ]

    # 关联
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='script_sessions',
        verbose_name='创作者'
    )
    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name='script_sessions',
        verbose_name='所属节目',
        null=True,
        blank=True,
        help_text='可选，如果已选择节目'
    )
    episode = models.OneToOneField(
        Episode,
        on_delete=models.SET_NULL,
        related_name='script_session',
        verbose_name='生成的单集',
        null=True,
        blank=True,
        help_text='生成音频后关联的Episode'
    )

    # 会话信息
    title = models.CharField('会话标题', max_length=255, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')

    # 对话历史 (JSON格式)
    # 格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    chat_history = models.JSONField('对话历史', default=list)

    # 当前脚本内容 (Markdown格式)
    current_script = models.TextField('当前脚本', blank=True, help_text='Markdown格式，包含【角色名】标签')

    # 脚本版本历史 (JSON格式)
    # 格式: [{"version": 1, "script": "...", "timestamp": "..."}, ...]
    script_versions = models.JSONField('脚本版本历史', default=list)

    # 音色配置 (JSON格式)
    # 格式: {"角色名": {"voice_id": "xxx", "voice_name": "罗翔"}, ...}
    voice_config = models.JSONField('音色配置', default=dict, blank=True)

    # 元数据
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'script_sessions'
        ordering = ['-updated_at']
        verbose_name = 'AI脚本会话'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.creator.username} - {self.title or '未命名会话'}"

    def add_message(self, role: str, content: str):
        """添加一条对话消息"""
        self.chat_history.append({
            'role': role,
            'content': content,
            'timestamp': models.DateTimeField(auto_now_add=True).isoformat()
        })
        self.save()

    def update_script(self, new_script: str):
        """更新脚本并保存版本"""
        # 保存旧版本
        if self.current_script:
            version = len(self.script_versions) + 1
            self.script_versions.append({
                'version': version,
                'script': self.current_script,
                'timestamp': models.DateTimeField(auto_now_add=True).isoformat()
            })

        # 更新当前脚本
        self.current_script = new_script
        self.save()


class UploadedReference(models.Model):
    """上传的参考文件 - 用于AI生成脚本时的参考材料"""

    FILE_TYPE_CHOICES = [
        ('txt', '文本文件'),
        ('pdf', 'PDF文档'),
        ('md', 'Markdown文档'),
        ('docx', 'Word文档'),
    ]

    session = models.ForeignKey(
        ScriptSession,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name='所属会话'
    )

    # 文件信息
    file = models.FileField('文件', upload_to='script_references/%Y/%m/')
    original_filename = models.CharField('原始文件名', max_length=255)
    file_type = models.CharField('文件类型', max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.BigIntegerField('文件大小', help_text='字节')

    # 提取的文本内容
    extracted_text = models.TextField('提取的文本', blank=True, help_text='从文件中提取的纯文本内容')

    # 元数据
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)

    class Meta:
        db_table = 'uploaded_references'
        ordering = ['-uploaded_at']
        verbose_name = '参考文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.original_filename} ({self.session.creator.username})"
