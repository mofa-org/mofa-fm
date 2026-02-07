"""
默认节目工具
"""
from __future__ import annotations

import base64

from django.core.files.base import ContentFile
from django.db import transaction

from apps.podcasts.models import Show


DEFAULT_SHOW_TITLE = "我的音频"
DEFAULT_SHOW_DESCRIPTION = "系统自动创建，用于快速生成与管理音频内容。"
DEFAULT_SHOW_SLUG_PREFIX = "audio-workbench"

# 1x1 PNG（透明）
_DEFAULT_COVER_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/m8kAAAAASUVORK5CYII="
)


def _default_show_slug(user_id: int) -> str:
    return f"{DEFAULT_SHOW_SLUG_PREFIX}-{user_id}"


def get_or_create_default_show(user):
    """
    获取或创建用户默认节目。
    """
    if not user or not getattr(user, "is_authenticated", False):
        raise ValueError("需要已登录用户")

    slug = _default_show_slug(user.id)
    existing = Show.objects.filter(creator=user, slug=slug).first()
    if existing:
        return existing, False

    cover_content = ContentFile(
        base64.b64decode(_DEFAULT_COVER_BASE64),
        name=f"default-show-{user.id}.png",
    )

    with transaction.atomic():
        show, created = Show.objects.get_or_create(
            creator=user,
            slug=slug,
            defaults={
                "title": DEFAULT_SHOW_TITLE,
                "description": DEFAULT_SHOW_DESCRIPTION,
                "cover": cover_content,
                "content_type": "podcast",
                "visibility": "public",
            },
        )
    return show, created
