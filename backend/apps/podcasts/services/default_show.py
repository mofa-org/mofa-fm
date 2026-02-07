"""
默认节目工具
"""
from __future__ import annotations

import base64
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from apps.podcasts.models import Show


LEGACY_DEFAULT_SHOW_TITLES = {"我的音频", "我的频道"}
DEFAULT_SHOW_DESCRIPTION = "系统自动创建，用于快速生成与管理音频内容。"
DEFAULT_SHOW_SLUG_PREFIX = "audio-workbench"

# 旧版 1x1 PNG（透明）
_LEGACY_TRANSPARENT_COVER_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/m8kAAAAASUVORK5CYII="
)
_LEGACY_TRANSPARENT_COVER_BYTES = base64.b64decode(_LEGACY_TRANSPARENT_COVER_BASE64)
_DEFAULT_SHOW_COVER_FILENAME = "default_show_logo.png"


def _default_show_slug(user_id: int) -> str:
    return f"{DEFAULT_SHOW_SLUG_PREFIX}-{user_id}"


def _default_show_title(user) -> str:
    username = (getattr(user, "username", "") or "").strip()
    if not username:
        username = f"用户{user.id}"
    return f"{username}的频道"[:255]


def _default_cover_bytes() -> bytes:
    candidate_paths = [
        Path(settings.BASE_DIR) / "static" / _DEFAULT_SHOW_COVER_FILENAME,
        Path(settings.BASE_DIR).parent / "frontend" / "public" / "logo.png",
    ]
    for path in candidate_paths:
        try:
            if path.exists() and path.is_file():
                data = path.read_bytes()
                if data:
                    return data
        except OSError:
            continue
    return _LEGACY_TRANSPARENT_COVER_BYTES


def _build_default_cover_content(user_id: int) -> ContentFile:
    return ContentFile(_default_cover_bytes(), name=f"default-show-{user_id}.png")


def _is_legacy_transparent_cover(show: Show) -> bool:
    if not show.cover:
        return True
    try:
        with show.cover.open("rb") as f:
            return f.read() == _LEGACY_TRANSPARENT_COVER_BYTES
    except OSError:
        return False


def get_or_create_default_show(user):
    """
    获取或创建用户默认节目。
    """
    if not user or not getattr(user, "is_authenticated", False):
        raise ValueError("需要已登录用户")

    slug = _default_show_slug(user.id)
    title = _default_show_title(user)
    existing = Show.objects.filter(creator=user, slug=slug).first()
    if existing:
        update_fields = []
        if existing.title in LEGACY_DEFAULT_SHOW_TITLES and existing.title != title:
            existing.title = title
            update_fields.append("title")
        if _is_legacy_transparent_cover(existing):
            existing.cover.save(
                f"default-show-{user.id}.png",
                _build_default_cover_content(user.id),
                save=False,
            )
            update_fields.append("cover")
        if update_fields:
            existing.save(update_fields=update_fields)
        return existing, False

    cover_content = _build_default_cover_content(user.id)

    with transaction.atomic():
        show, created = Show.objects.get_or_create(
            creator=user,
            slug=slug,
            defaults={
                "title": title,
                "description": DEFAULT_SHOW_DESCRIPTION,
                "cover": cover_content,
                "content_type": "podcast",
                "visibility": "public",
            },
        )
    return show, created
