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
    Apply role-tag name replacement in script using LLM for better context understanding.
    e.g.: 【大牛】 -> 【自定义主持名】, and "我是大牛" -> "我是小牛"
    """
    if not script_content:
        return script_content

    config = normalize_speaker_config(speaker_config)
    if not config:
        return script_content

    # 如果没有自定义名称，直接返回原脚本
    host_name = config["host_name"]
    guest_name = config["guest_name"]
    judge_name = config["judge_name"]
    if (host_name == DEFAULT_HOST_NAME and
        guest_name == DEFAULT_GUEST_NAME and
        judge_name == DEFAULT_JUDGE_NAME):
        return script_content

    # 使用 LLM 改写脚本，统一称谓
    try:
        from openai import OpenAI
        from django.conf import settings

        client = OpenAI(
            api_key=getattr(settings, 'OPENAI_API_KEY', ''),
            base_url=getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1')
        )
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

        prompt = f"""请将以下播客脚本中的角色名称统一替换。只替换角色名称，其他内容保持不变。

原角色名 -> 新角色名：
- 大牛 -> {host_name}
- 一帆 -> {guest_name}
- 博宇 -> {judge_name}

注意：
1. 替换所有出现的角色名，包括中括号内的标记和正文中的称呼
2. 保持脚本格式不变（【角色名】对话内容）
3. 只返回改写后的脚本，不要添加任何解释

原脚本：
{script_content}
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的文本编辑助手，擅长统一文本中的角色名称。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )

        result = response.choices[0].message.content.strip()
        # 如果 LLM 返回了 markdown 代码块，提取其中的内容
        if result.startswith("```"):
            result = re.sub(r"^```\w*\n?|```$", "", result, flags=re.MULTILINE).strip()
        return result

    except Exception as e:
        # LLM 失败时回退到简单的正则替换
        print(f"LLM rewrite failed: {e}, falling back to regex replacement")
        result = script_content
        result = re.sub(r"【\s*大牛\s*】", lambda _m: f"【{host_name}】", result)
        result = re.sub(r"【\s*一帆\s*】", lambda _m: f"【{guest_name}】", result)
        result = re.sub(r"【\s*博宇\s*】", lambda _m: f"【{judge_name}】", result)
        result = re.sub(r"大牛", host_name, result)
        result = re.sub(r"一帆", guest_name, result)
        result = re.sub(r"博宇", judge_name, result)
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

