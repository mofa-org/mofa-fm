"""
Fetch and cache MiniMax TTS voice catalog.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


MINIMAX_GET_VOICE_URL = "https://api.minimax.io/v1/get_voice"
VOICE_CACHE_TTL_SECONDS = 3600

LEGACY_DEFAULT_VOICES: List[Dict[str, str]] = [
    {
        "voice_id": "Chinese (Mandarin)_News_Anchor",
        "voice_name": "大牛（新闻主播）",
        "language": "zh",
        "source": "legacy_default",
    },
    {
        "voice_id": "Chinese (Mandarin)_Gentleman",
        "voice_name": "一帆（绅士）",
        "language": "zh",
        "source": "legacy_default",
    },
    {
        "voice_id": "Chinese (Mandarin)_Radio_Host",
        "voice_name": "博宇（电台主持人）",
        "language": "zh",
        "source": "legacy_default",
    },
]


def _infer_language(voice_id: str, voice_name: str) -> str:
    value = f"{voice_id} {voice_name}"
    if "Chinese (Mandarin)" in value or re.search(r"[\u4e00-\u9fff]", value):
        return "zh"
    if "English" in value:
        return "en"
    return "other"


def _normalize_voice_item(item: Dict[str, object], source: str) -> Dict[str, object]:
    voice_id = str(item.get("voice_id") or "").strip()
    voice_name = str(item.get("voice_name") or voice_id).strip()
    description = item.get("description") or []
    if isinstance(description, list):
        description_text = " ".join(str(x) for x in description if x)
    else:
        description_text = str(description or "")

    return {
        "voice_id": voice_id,
        "voice_name": voice_name,
        "language": _infer_language(voice_id, voice_name),
        "description": description_text,
        "source": source,
    }


def _dedupe_voices(voices: List[Dict[str, object]]) -> List[Dict[str, object]]:
    seen = set()
    result = []
    for voice in voices:
        voice_id = str(voice.get("voice_id") or "").strip()
        if not voice_id or voice_id in seen:
            continue
        seen.add(voice_id)
        result.append(voice)
    return result


def get_available_tts_voices(language: str = "zh", force_refresh: bool = False) -> Dict[str, object]:
    language = (language or "zh").lower()
    cache_key = f"podcasts:tts:voices:{language}"

    if not force_refresh:
        cached = cache.get(cache_key)
        if cached:
            return cached

    api_key = settings.MINIMAX_TTS.get("api_key") or os.getenv("MINIMAX_API_KEY")
    if not api_key:
        result = {
            "source": "fallback",
            "message": "MINIMAX_API_KEY 未配置，返回默认音色",
            "updated_at": timezone.now().isoformat(),
            "voices": LEGACY_DEFAULT_VOICES,
            "count": len(LEGACY_DEFAULT_VOICES),
        }
        cache.set(cache_key, result, VOICE_CACHE_TTL_SECONDS)
        return result

    voices: List[Dict[str, object]] = []
    source = "minimax"
    message = "success"

    try:
        response = requests.post(
            MINIMAX_GET_VOICE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"voice_type": "all"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        status_code = (payload.get("base_resp") or {}).get("status_code", -1)
        if status_code != 0:
            raise ValueError((payload.get("base_resp") or {}).get("status_msg") or "MiniMax get_voice failed")

        voices.extend(_normalize_voice_item(item, source="system_voice") for item in (payload.get("system_voice") or []))
        voices.extend(_normalize_voice_item(item, source="voice_cloning") for item in (payload.get("voice_cloning") or []))
        voices.extend(_normalize_voice_item(item, source="voice_generation") for item in (payload.get("voice_generation") or []))
    except Exception as exc:
        source = "fallback"
        message = f"MiniMax get_voice failed: {exc}"
        voices = []

    voices = _dedupe_voices(voices)

    if language == "zh":
        zh_voices = [voice for voice in voices if voice.get("language") == "zh"]
        if zh_voices:
            voices = zh_voices

    legacy_items = [_normalize_voice_item(item, source=item.get("source", "legacy_default")) for item in LEGACY_DEFAULT_VOICES]
    voices = _dedupe_voices(legacy_items + voices)
    voices.sort(key=lambda item: (str(item.get("language") or ""), str(item.get("voice_name") or "")))

    result = {
        "source": source,
        "message": message,
        "updated_at": timezone.now().isoformat(),
        "voices": voices,
        "count": len(voices),
    }
    cache.set(cache_key, result, VOICE_CACHE_TTL_SECONDS)
    return result

