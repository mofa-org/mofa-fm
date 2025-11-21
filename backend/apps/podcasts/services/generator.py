"""
Podcast audio generator that streams MiniMax TTS output, inspired by the
MoFA `podcast-generator` flow (flows/podcast-generator).
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import re
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from pydub import AudioSegment

from .minimax_client import MiniMaxError, MiniMaxVoiceConfig, synthesize_to_pcm

logger = logging.getLogger(__name__)

DEFAULT_PUNCTUATION_MARKS = "。？！!?；；…"


def _coerce_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _find_split_index(text: str, max_length: int, split_marks: str) -> int:
    if max_length <= 0:
        return -1

    limit = min(len(text), max_length)
    marks = set(split_marks or "")

    for idx in range(limit, 0, -1):
        if text[idx - 1] in marks:
            return idx

    for idx in range(limit, 0, -1):
        if text[idx - 1].isspace():
            return idx

    return -1


def _split_long_text(text: str, max_length: int, punctuation_marks: str) -> List[str]:
    if max_length <= 0 or len(text) <= max_length:
        return [text]

    segments: List[str] = []
    remainder = text.strip()

    while remainder:
        if len(remainder) <= max_length:
            segments.append(remainder)
            break

        split_idx = _find_split_index(remainder, max_length, punctuation_marks)
        if split_idx == -1:
            split_idx = max_length

        chunk = remainder[:split_idx].strip()
        if chunk:
            segments.append(chunk)
        remainder = remainder[split_idx:].lstrip()

    return segments


class PodcastGenerator:
    """
    Generate two-person podcast audio using MiniMax streaming TTS.

    Behaviour mirrors the Dora flow under `mofa/flows/podcast-generator`
    so that output timing, speaker handling, and silence padding remain
    consistent with the CLI workflow.
    """

    DEFAULT_VOICES: Dict[str, Dict[str, object]] = {
        "daniu": {
            "voice_id": "ttv-voice-2025103011222725-sg8dZxUP",
            "speed": 1.0,
            "volume": 1.0,
            "pitch": -1,
        },
        "yifan": {
            "voice_id": "moss_audio_aaa1346a-7ce7-11f0-8e61-2e6e3c7ee85d",
            "speed": 1.0,
            "volume": 1.0,
            "pitch": 0,
        },
    }

    CHARACTER_ALIASES: Dict[str, str] = {
        "大牛": "daniu",
        "一帆": "yifan",
    }

    def __init__(self):
        minimax_settings = getattr(settings, "MINIMAX_TTS", {})

        self.api_key = minimax_settings.get("api_key") or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise MiniMaxError("MINIMAX_API_KEY 未配置，请在环境变量或 settings.MINIMAX_TTS 中添加")

        self.model = minimax_settings.get("model", "speech-2.5-hd-preview")
        self.sample_rate = int(minimax_settings.get("sample_rate", 32000))
        self.audio_bitrate = int(minimax_settings.get("audio_bitrate", 128000))
        self.audio_channel = int(minimax_settings.get("audio_channel", 1))
        self.enable_english_normalization = _coerce_bool(
            minimax_settings.get("enable_english_normalization"), True
        )

        self.max_segment_chars = int(minimax_settings.get("max_segment_chars", 120))
        self.punctuation_marks = minimax_settings.get("punctuation_marks", DEFAULT_PUNCTUATION_MARKS)

        self.silence_min_ms = int(minimax_settings.get("silence_min_ms", 300))
        self.silence_max_ms = int(minimax_settings.get("silence_max_ms", 1200))
        if self.silence_min_ms < 0 or self.silence_max_ms < self.silence_min_ms:
            raise ValueError("MiniMax 静音区间配置不正确，请检查 silence_min_ms / silence_max_ms")

        aliases = minimax_settings.get("aliases", {})
        if isinstance(aliases, dict):
            self.character_aliases = {**self.CHARACTER_ALIASES, **aliases}
        else:
            self.character_aliases = dict(self.CHARACTER_ALIASES)

        voice_overrides = minimax_settings.get("voices", {}) or {}
        self.voice_configs: Dict[str, MiniMaxVoiceConfig] = {}

        def build_config(alias: str, data: Dict[str, object]) -> MiniMaxVoiceConfig:
            override = voice_overrides.get(alias, {})
            return MiniMaxVoiceConfig(
                api_key=self.api_key,
                model=override.get("model", self.model),
                voice_id=override.get("voice_id", data.get("voice_id", "")),
                speed=float(override.get("speed", data.get("speed", 1.0))),
                volume=float(override.get("volume", data.get("volume", 1.0))),
                pitch=int(override.get("pitch", data.get("pitch", 0))),
                sample_rate=int(override.get("sample_rate", self.sample_rate)),
                audio_bitrate=int(override.get("audio_bitrate", self.audio_bitrate)),
                audio_channel=int(override.get("audio_channel", self.audio_channel)),
                enable_english_normalization=_coerce_bool(
                    override.get(
                        "enable_english_normalization",
                        self.enable_english_normalization,
                    ),
                    self.enable_english_normalization,
                ),
            )

        for alias, data in self.DEFAULT_VOICES.items():
            config = build_config(alias, data)
            self.voice_configs[alias] = config

        # Allow defining entirely new voices via settings
        for alias, override in voice_overrides.items():
            if alias in self.voice_configs:
                continue
            config = MiniMaxVoiceConfig(
                api_key=self.api_key,
                model=override.get("model", self.model),
                voice_id=override.get("voice_id", ""),
                speed=float(override.get("speed", 1.0)),
                volume=float(override.get("volume", 1.0)),
                pitch=int(override.get("pitch", 0)),
                sample_rate=int(override.get("sample_rate", self.sample_rate)),
                audio_bitrate=int(override.get("audio_bitrate", self.audio_bitrate)),
                audio_channel=int(override.get("audio_channel", self.audio_channel)),
                enable_english_normalization=_coerce_bool(
                    override.get("enable_english_normalization", self.enable_english_normalization),
                    self.enable_english_normalization,
                ),
            )
            self.voice_configs[alias] = config

    def generate(self, script_content: str, output_path: str) -> str:
        logger.info("MiniMax 播客生成开始")

        segments = self._parse_markdown(script_content)
        segments = self._expand_segments(segments)

        if not segments:
            raise ValueError("脚本中未找到有效的角色对话内容")

        logger.info("共解析 %s 个语音片段", len(segments))

        try:
            audio_segments = asyncio.run(self._generate_all_segments(segments))
        except Exception as exc:
            logger.exception("调用 MiniMax 生成音频失败: %s", exc)
            raise

        if not audio_segments:
            raise ValueError("MiniMax 未生成任何音频片段")

        final_audio = AudioSegment.silent(duration=0)
        last_speaker: Optional[str] = None

        for speaker, audio_chunk in audio_segments:
            if last_speaker and last_speaker != speaker:
                silence = random.randint(self.silence_min_ms, self.silence_max_ms)
                final_audio += AudioSegment.silent(duration=silence)
                logger.debug("插入静音 %sms (%s → %s)", silence, last_speaker, speaker)

            final_audio += audio_chunk
            last_speaker = speaker

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_audio.export(output_path, format="mp3")
        logger.info("MiniMax 播客生成完成，输出路径: %s", output_path)

        return output_path

    def _parse_markdown(self, script_content: str) -> List[Tuple[str, str]]:
        segments: List[Tuple[str, str]] = []
        current_character: Optional[str] = None
        current_text: List[str] = []

        def finalize_segment() -> None:
            nonlocal current_character, current_text
            if current_character and current_text:
                combined = " ".join(current_text).strip()
                if combined:
                    segments.append((current_character, combined))
            current_text = []

        for raw_line in script_content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            match = re.search(r"【([^】]+)】", line)
            if match:
                finalize_segment()
                tag_content = match.group(1).strip()

                character = self.character_aliases.get(tag_content)
                if not character:
                    lowered = tag_content.lower()
                    character = self.voice_configs.get(lowered) and lowered

                if not character:
                    logger.debug("跳过未知角色: %s", tag_content)
                    current_character = None
                    current_text = []
                    continue

                remainder = line.split("】", 1)[1] if "】" in line else ""
                remainder = remainder.lstrip("*").strip()

                current_character = character
                current_text = [remainder] if remainder else []
                continue

            if current_character:
                clean_line = line.strip("*").strip()
                if clean_line:
                    current_text.append(clean_line)

        finalize_segment()
        return segments

    def _expand_segments(self, segments: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        expanded: List[Tuple[str, str]] = []
        for speaker, text in segments:
            voice_config = self.voice_configs.get(speaker)
            if not voice_config:
                logger.warning("未配置 %s 的语音，跳过该段落", speaker)
                continue

            parts = _split_long_text(text, self.max_segment_chars, self.punctuation_marks)
            expanded.extend((speaker, part) for part in parts if part)

        return expanded

    async def _generate_all_segments(self, segments: List[Tuple[str, str]]) -> List[Tuple[str, AudioSegment]]:
        results: List[Tuple[str, AudioSegment]] = []

        for index, (speaker, text) in enumerate(segments, start=1):
            config = self.voice_configs.get(speaker)
            if not config:
                logger.warning("跳过未配置语音的角色 %s", speaker)
                continue

            logger.info("MiniMax 生成片段 %s/%s (%s)", index, len(segments), speaker)

            def client_logger(message: str, *, _speaker=speaker, _index=index):
                logger.debug("[MiniMax][%s #%s] %s", _speaker, _index, message)

            sample_rate, pcm_bytes = await synthesize_to_pcm(config, text, logger=client_logger)

            segment_audio = AudioSegment(
                data=pcm_bytes,
                sample_width=2,
                frame_rate=sample_rate,
                channels=config.audio_channel,
            )
            results.append((speaker, segment_audio))

        return results
