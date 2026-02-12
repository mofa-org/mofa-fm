"""
播客模型
"""
from datetime import time as dt_time

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

    VISIBILITY_CHOICES = [
        ('public', '公开'),
        ('unlisted', '不公开列出（仅链接可访问）'),
        ('followers', '仅关注者'),
        ('private', '私有'),
        ('shared', '仅受邀用户'),
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

    # 可见性控制
    visibility = models.CharField(
        '可见性',
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='public',
        db_index=True,
        help_text='控制谁可以看到这个节目'
    )
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_shows',
        verbose_name='共享给用户',
        help_text='当可见性为"仅受邀用户"时生效'
    )

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

    @property
    def cover_url(self):
        """获取封面URL"""
        if self.cover:
            return self.cover.url
        return '/static/default_show_logo.png'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = awesome_slugify(self.title)
        super().save(*args, **kwargs)

    def can_view(self, user):
        """检查用户是否可以查看此节目"""
        # 未激活的节目只有创作者能看
        if not self.is_active and (not user or user != self.creator):
            return False

        # 私有：仅创作者
        if self.visibility == 'private':
            return user and user == self.creator

        # 仅受邀用户：创作者 + 受邀用户
        if self.visibility == 'shared':
            if not user:
                return False
            return user == self.creator or self.shared_with.filter(id=user.id).exists()

        # 仅关注者：创作者 + 关注者
        if self.visibility == 'followers':
            if not user:
                return False
            if user == self.creator:
                return True
            return self.followers.filter(user=user).exists()

        # 不公开列出：任何知道链接的人都能访问
        if self.visibility == 'unlisted':
            return True

        # 公开：所有人
        return True

    def is_visible_in_list(self, user):
        """检查节目是否应该在列表中显示"""
        # 只有公开的节目才会在列表中显示
        if self.visibility != 'public':
            # 但创作者自己能看到自己的所有节目
            return user and user == self.creator
        return self.is_active


class Episode(models.Model):
    """播客单集/音乐单曲"""

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('processing', '处理中'),
        ('published', '已发布'),
        ('failed', '处理失败'),
    ]

    VISIBILITY_CHOICES = [
        ('inherit', '继承节目设置'),
        ('public', '公开'),
        ('unlisted', '不公开列出（仅链接可访问）'),
        ('followers', '仅关注者'),
        ('private', '私有'),
        ('shared', '仅受邀用户'),
    ]

    MODE_CHOICES = [
        ('podcast', '播客'),
        ('debate', '辩论'),
        ('conference', '会议'),
    ]

    GENERATION_STAGE_CHOICES = [
        ('queued', '排队中'),
        ('source_fetching', '抓取中'),
        ('script_generating', '写稿中'),
        ('audio_generating', '音频生成中'),
        ('cover_generating', '封面生成中'),
        ('completed', '完成'),
        ('failed', '失败'),
    ]

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name='episodes',
        verbose_name='播客节目',
        null=True,
        blank=True,
        help_text='Debate/Conference模式可为空，发布音频时再关联'
    )
    title = models.CharField('标题', max_length=255, db_index=True)
    slug = models.SlugField('URL标识', max_length=255)
    description = models.TextField('描述')
    cover = models.ImageField('封面', upload_to='episode_covers/%Y/%m/', blank=True, null=True)

    # 可见性控制（可覆盖节目级别设置）
    visibility = models.CharField(
        '可见性',
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='inherit',
        db_index=True,
        help_text='inherit 表示继承节目的可见性设置'
    )
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_episodes',
        verbose_name='共享给用户',
        help_text='当可见性为"仅受邀用户"时生效'
    )

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
    generation_stage = models.CharField(
        '生成阶段',
        max_length=32,
        choices=GENERATION_STAGE_CHOICES,
        default='queued',
        db_index=True
    )
    generation_error = models.TextField('生成错误信息', blank=True, default='')
    generation_meta = models.JSONField('生成元数据', default=dict, blank=True)

    # 生成模式（新增字段）
    mode = models.CharField(
        '生成模式',
        max_length=20,
        choices=MODE_CHOICES,
        default='podcast',
        db_index=True,
        help_text='podcast: 传统播客, debate: AI辩论, conference: AI会议'
    )

    # 脚本内容（可编辑，用于TTS微调）
    script = models.TextField('脚本', blank=True, help_text='Markdown格式，包含【角色名】标签，创作者可编辑以调整TTS发音')

    # 对话记录（仅debate/conference模式使用）
    dialogue = models.JSONField(
        '对话记录',
        null=True,
        blank=True,
        help_text='流式对话记录，格式: [{"participant": "llm1", "content": "...", "timestamp": "..."}, ...]'
    )

    # 参与者配置（仅debate/conference模式使用）
    participants_config = models.JSONField(
        '参与者配置',
        null=True,
        blank=True,
        help_text='参与者角色和system prompt配置'
    )

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
            base_slug = awesome_slugify(self.title)
            # Ensure unique slug within the show
            slug = base_slug
            counter = 1
            while Episode.objects.filter(show=self.show, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
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
        if self.show and self.show.cover:
            return self.show.cover.url
        return '/static/default_show_logo.png'

    def get_effective_visibility(self):
        """获取实际生效的可见性（考虑继承）"""
        if self.visibility == 'inherit':
            return self.show.visibility
        return self.visibility

    def can_view(self, user):
        """检查用户是否可以查看此单集"""
        # 未发布的单集只有创作者能看
        if self.status != 'published' and (not user or user != self.show.creator):
            return False

        # 首先检查节目级别权限
        if not self.show.can_view(user):
            return False

        # 如果继承节目设置，直接返回节目权限
        if self.visibility == 'inherit':
            return True

        # 否则检查单集自己的可见性设置
        visibility = self.visibility

        # 私有：仅创作者
        if visibility == 'private':
            return user and user == self.show.creator

        # 仅受邀用户：创作者 + 受邀用户
        if visibility == 'shared':
            if not user:
                return False
            return user == self.show.creator or self.shared_with.filter(id=user.id).exists()

        # 仅关注者：创作者 + 关注者
        if visibility == 'followers':
            if not user:
                return False
            if user == self.show.creator:
                return True
            return self.show.followers.filter(user=user).exists()

        # 不公开列出、公开：都可访问
        return True

    def is_visible_in_list(self, user):
        """检查单集是否应该在列表中显示"""
        visibility = self.get_effective_visibility()

        # 只有公开的单集才会在列表中显示
        if visibility != 'public':
            # 但创作者自己能看到自己的所有单集
            return user and user == self.show.creator

        return self.status == 'published'


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
        from django.utils import timezone
        self.chat_history.append({
            'role': role,
            'content': content,
            'timestamp': timezone.now().isoformat()
        })
        self.save()

    def update_script(self, new_script: str):
        """更新脚本并保存版本"""
        from django.utils import timezone
        # 保存旧版本
        if self.current_script:
            version = len(self.script_versions) + 1
            self.script_versions.append({
                'version': version,
                'script': self.current_script,
                'timestamp': timezone.now().isoformat()
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


class RSSSource(models.Model):
    """用户维护的 RSS 源"""

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rss_sources',
        verbose_name='用户',
    )
    name = models.CharField('名称', max_length=120)
    url = models.URLField('RSS 地址', max_length=500)
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'rss_sources'
        ordering = ['-updated_at']
        unique_together = [['creator', 'url']]
        indexes = [
            models.Index(fields=['creator', 'is_active']),
            models.Index(fields=['-updated_at']),
        ]
        verbose_name = 'RSS 源'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} ({self.creator.username})"


class RSSList(models.Model):
    """用户维护的 RSS 源列表"""

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rss_lists',
        verbose_name='用户',
    )
    name = models.CharField('列表名', max_length=120)
    description = models.TextField('描述', blank=True)
    sources = models.ManyToManyField(
        RSSSource,
        blank=True,
        related_name='rss_lists',
        verbose_name='源',
    )
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'rss_lists'
        ordering = ['-updated_at']
        unique_together = [['creator', 'name']]
        indexes = [
            models.Index(fields=['creator', 'is_active']),
            models.Index(fields=['-updated_at']),
        ]
        verbose_name = 'RSS 列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} ({self.creator.username})"


class RSSSchedule(models.Model):
    """RSS 自动化定时规则"""

    FREQUENCY_CHOICES = [
        ('daily', '每天'),
        ('weekly', '每周'),
    ]
    STATUS_CHOICES = [
        ('idle', '空闲'),
        ('queued', '排队中'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]
    SORT_CHOICES = [
        ('latest', 'latest'),
        ('oldest', 'oldest'),
        ('title', 'title'),
    ]

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rss_schedules',
        verbose_name='用户',
    )
    name = models.CharField('规则名', max_length=120)
    rss_list = models.ForeignKey(
        RSSList,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='RSS 列表',
    )
    show = models.ForeignKey(
        Show,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rss_schedules',
        verbose_name='目标频道',
    )

    template = models.CharField('模板', max_length=32, default='news_flash')
    max_items = models.PositiveSmallIntegerField('抓取条数', default=8)
    deduplicate = models.BooleanField('去重', default=True)
    sort_by = models.CharField('排序', max_length=12, choices=SORT_CHOICES, default='latest')

    host_name = models.CharField('主持名', max_length=64, blank=True, default='')
    guest_name = models.CharField('嘉宾名', max_length=64, blank=True, default='')
    host_voice_id = models.CharField('主持音色ID', max_length=128, blank=True, default='')
    guest_voice_id = models.CharField('嘉宾音色ID', max_length=128, blank=True, default='')

    timezone_name = models.CharField('时区', max_length=64, default='Asia/Shanghai')
    run_time = models.TimeField('执行时间', default=dt_time(hour=8, minute=0))
    frequency = models.CharField('频率', max_length=12, choices=FREQUENCY_CHOICES, default='daily')
    week_days = models.JSONField('每周执行日', default=list, blank=True, help_text='0-6, 周一到周日')

    is_active = models.BooleanField('启用', default=True)
    next_run_at = models.DateTimeField('下次执行时间', null=True, blank=True, db_index=True)
    last_run_at = models.DateTimeField('上次执行时间', null=True, blank=True)
    last_status = models.CharField('最近状态', max_length=20, choices=STATUS_CHOICES, default='idle')
    last_error = models.TextField('最近错误', blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'rss_schedules'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['creator', 'is_active']),
            models.Index(fields=['is_active', 'next_run_at']),
            models.Index(fields=['-updated_at']),
        ]
        verbose_name = 'RSS 定时规则'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} ({self.creator.username})"


class RSSRun(models.Model):
    """RSS 定时任务运行记录"""

    STATUS_CHOICES = [
        ('queued', '排队中'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]
    TRIGGER_CHOICES = [
        ('auto', '自动触发'),
        ('manual', '手动触发'),
    ]

    schedule = models.ForeignKey(
        RSSSchedule,
        on_delete=models.CASCADE,
        related_name='runs',
        verbose_name='规则',
    )
    episode = models.ForeignKey(
        Episode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rss_runs',
        verbose_name='生成单集',
    )
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='queued')
    trigger_type = models.CharField('触发方式', max_length=20, choices=TRIGGER_CHOICES, default='auto')
    message = models.TextField('说明', blank=True)
    error = models.TextField('错误', blank=True)
    item_count = models.IntegerField('条目数', default=0)
    meta = models.JSONField('元数据', default=dict, blank=True)
    started_at = models.DateTimeField('开始时间', auto_now_add=True)
    finished_at = models.DateTimeField('结束时间', null=True, blank=True)

    class Meta:
        db_table = 'rss_runs'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['schedule', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
        verbose_name = 'RSS 运行记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.schedule.name} - {self.get_status_display()}"
