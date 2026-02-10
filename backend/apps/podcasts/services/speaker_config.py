"""
Speaker (角色名/音色) runtime helpers for podcast generation.
"""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple


DEFAULT_HOST_NAME = "大牛"
DEFAULT_GUEST_NAME = "一帆"
DEFAULT_JUDGE_NAME = "博宇"
DEFAULT_HOST_ALIAS = "daniu"
DEFAULT_GUEST_ALIAS = "yifan"
DEFAULT_JUDGE_ALIAS = "boyu"


def normalize_speaker_config(raw: Optional[dict]) -> Optional[dict]:
    """
    Normalize user-provided speaker config.
    Supports 3 roles: host, guest, judge (for debate/conference mode)

    Returns None when no config is effectively provided.
    """
    if not isinstance(raw, dict):
        return None

    host_name = str(raw.get("host_name") or "").strip()
    guest_name = str(raw.get("guest_name") or "").strip()
    judge_name = str(raw.get("judge_name") or "").strip()
    host_voice_id = str(raw.get("host_voice_id") or "").strip()
    guest_voice_id = str(raw.get("guest_voice_id") or "").strip()
    judge_voice_id = str(raw.get("judge_voice_id") or "").strip()

    if not any([host_name, guest_name, judge_name, host_voice_id, guest_voice_id, judge_voice_id]):
        return None

    return {
        "host_name": host_name or DEFAULT_HOST_NAME,
        "guest_name": guest_name or DEFAULT_GUEST_NAME,
        "judge_name": judge_name or DEFAULT_JUDGE_NAME,
        "host_voice_id": host_voice_id,
        "guest_voice_id": guest_voice_id,
        "judge_voice_id": judge_voice_id,
    }


def apply_speaker_names(script_content: str, speaker_config: Optional[dict]) -> str:
    """
    Apply role-tag name replacement in script, e.g.:
    【大牛】 -> 【自定义主持名】
    【一帆】 -> 【自定义嘉宾名】
    【博宇】 -> 【自定义主持人/导师名】
    """
    if not script_content:
        return script_content

    config = normalize_speaker_config(speaker_config)
    if not config:
        return script_content

    result = script_content
    host_name = config["host_name"]
    guest_name = config["guest_name"]
    judge_name = config["judge_name"]

    result = re.sub(r"【\s*大牛\s*】", lambda _m: f"【{host_name}】", result)
    result = re.sub(r"【\s*一帆\s*】", lambda _m: f"【{guest_name}】", result)
    result = re.sub(r"【\s*博宇\s*】", lambda _m: f"【{judge_name}】", result)
    return result


def build_generator_runtime_options(
    speaker_config: Optional[dict],
) -> Tuple[Dict[str, str], Dict[str, Dict[str, object]]]:
    """
    Build runtime alias mapping + voice overrides for PodcastGenerator.
    Supports 3 roles: host, guest, judge (for debate/conference mode)
    """
    config = normalize_speaker_config(speaker_config)

    character_aliases: Dict[str, str] = {
        DEFAULT_HOST_NAME: DEFAULT_HOST_ALIAS,
        DEFAULT_GUEST_NAME: DEFAULT_GUEST_ALIAS,
        DEFAULT_JUDGE_NAME: DEFAULT_JUDGE_ALIAS,
    }
    voice_overrides: Dict[str, Dict[str, object]] = {}

    if not config:
        return character_aliases, voice_overrides

    host_name = config["host_name"]
    guest_name = config["guest_name"]
    judge_name = config["judge_name"]
    host_voice_id = config.get("host_voice_id") or ""
    guest_voice_id = config.get("guest_voice_id") or ""
    judge_voice_id = config.get("judge_voice_id") or ""

    character_aliases[host_name] = DEFAULT_HOST_ALIAS
    character_aliases[guest_name] = DEFAULT_GUEST_ALIAS
    character_aliases[judge_name] = DEFAULT_JUDGE_ALIAS

    if host_voice_id:
        voice_overrides[DEFAULT_HOST_ALIAS] = {"voice_id": host_voice_id}
    if guest_voice_id:
        voice_overrides[DEFAULT_GUEST_ALIAS] = {"voice_id": guest_voice_id}
    if judge_voice_id:
        voice_overrides[DEFAULT_JUDGE_ALIAS] = {"voice_id": judge_voice_id}

    return character_aliases, voice_overrides

