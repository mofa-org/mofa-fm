"""
Simple AI cover generation for podcast episodes.
"""
from __future__ import annotations

import base64
import re
from uuid import uuid4
from urllib.parse import quote_plus

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


def _build_prompt(title: str, script: str) -> str:
    snippet = (script or "").strip().replace("\n", " ")
    snippet = snippet[:120]
    return (
        "podcast cover illustration, abstract, modern, high contrast, no text, "
        f"topic {title}, vibe {snippet}"
    )


def _generate_with_openai(prompt: str) -> bytes:
    from openai import OpenAI

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY missing")

    client = OpenAI(
        api_key=api_key,
        base_url=getattr(settings, "OPENAI_API_BASE", "https://api.openai.com/v1"),
    )
    model = getattr(settings, "OPENAI_IMAGE_MODEL", "gpt-image-1")
    result = client.images.generate(model=model, prompt=prompt, size="1024x1024")
    b64 = result.data[0].b64_json
    if not b64:
        raise ValueError("Image generation returned empty data")
    return base64.b64decode(b64)


def _generate_with_openrouter_chat(prompt: str) -> bytes:
    """
    OpenRouter image-capable models return image data via chat/completions.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    api_base = getattr(settings, "OPENAI_API_BASE", "")
    if not api_key or "openrouter.ai" not in api_base:
        raise ValueError("openrouter config missing")

    model = getattr(settings, "OPENAI_IMAGE_MODEL", "openai/gpt-5-image-mini")
    url = f"{api_base.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["text", "image"],
    }
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    images = (((data.get("choices") or [{}])[0].get("message") or {}).get("images") or [])
    if not images:
        raise ValueError("OpenRouter returned no images")
    image_url = ((images[0].get("image_url") or {}).get("url") or "").strip()
    m = re.match(r"^data:image/\w+;base64,(.+)$", image_url, re.S)
    if not m:
        raise ValueError("OpenRouter image url is not base64 data URL")
    return base64.b64decode(m.group(1))


def _generate_with_pollinations(prompt: str) -> bytes:
    # Lightweight fallback if OpenAI-compatible image endpoint is unavailable.
    candidates = [
        prompt[:160],
        "podcast cover illustration abstract colorful no text",
        "cat",
    ]
    last_error = None
    for text in candidates:
        url = f"https://image.pollinations.ai/prompt/{quote_plus(text)}?width=512&height=512&nologo=true"
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            if resp.content:
                return resp.content
        except Exception as exc:
            last_error = exc
            continue
    raise last_error or RuntimeError("pollinations failed")


def _generate_cover_bytes(prompt: str) -> bytes | None:
    image_bytes = None
    try:
        image_bytes = _generate_with_openrouter_chat(prompt)
    except Exception:
        try:
            image_bytes = _generate_with_openai(prompt)
        except Exception:
            pass

    if not image_bytes:
        try:
            image_bytes = _generate_with_pollinations(prompt)
        except Exception:
            return None

    return image_bytes


def generate_episode_cover_candidates(episode, count: int = 4):
    count = max(1, min(int(count or 4), 8))
    prompt = _build_prompt(title=episode.title, script=episode.script or "")
    storage = episode.cover.storage
    date_prefix = timezone.now().strftime('%Y/%m')

    candidates = []
    for index in range(count):
        variant_prompt = f"{prompt}, variation {index + 1}"
        image_bytes = _generate_cover_bytes(variant_prompt)
        if not image_bytes:
            continue
        path = f"episode_cover_candidates/{date_prefix}/cand-{episode.id}-{uuid4().hex}.png"
        storage.save(path, ContentFile(image_bytes))
        candidates.append({
            "path": path,
            "url": storage.url(path),
        })

    return candidates


def apply_episode_cover_candidate(episode, candidate_path: str) -> str:
    if not candidate_path or not candidate_path.startswith("episode_cover_candidates/"):
        raise ValueError("candidate_path invalid")

    storage = episode.cover.storage
    if not storage.exists(candidate_path):
        raise ValueError("candidate file not found")

    with storage.open(candidate_path, "rb") as f:
        image_bytes = f.read()

    filename = f"ai-cover-{episode.slug or episode.id}-{episode.id}.png"
    episode.cover.save(filename, ContentFile(image_bytes), save=False)
    episode.save(update_fields=["cover", "updated_at"])
    return episode.cover.url


def generate_episode_cover(episode) -> bool:
    prompt = _build_prompt(title=episode.title, script=episode.script or "")
    image_bytes = _generate_cover_bytes(prompt)
    if not image_bytes:
        return False

    filename = f"ai-cover-{episode.slug or episode.id}-{episode.id}.png"
    episode.cover.save(filename, ContentFile(image_bytes), save=False)
    episode.save(update_fields=["cover", "updated_at"])
    return True
