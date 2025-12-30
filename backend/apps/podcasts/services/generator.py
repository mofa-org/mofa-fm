"""
Podcast audio generator that streams MiniMax TTS output, inspired by the
MoFA `podcast-generator` flow (flows/podcast-generator).

Updated to match MoFA Flow logic exactly:
- Time-based text segmentation (instead of fixed character count)
- Float32 audio processing with batching
- Enhanced punctuation handling
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import re
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings
from pydub import AudioSegment

from .minimax_client import MiniMaxError, MiniMaxVoiceConfig, synthesize_to_pcm

logger = logging.getLogger(__name__)

# MoFA Flow default punctuation marks (more comprehensive)
DEFAULT_PUNCTUATION_MARKS = "。！？.!?，,、；;：:"


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
    """
    Find a split index at or before max_length using provided marks or whitespace.

    Copied from MoFA Flow script_segmenter for sentence-aware splitting.
    """
    if max_length <= 0:
        return -1

    limit = min(len(text), max_length)

    # Try to split at punctuation marks first
    if split_marks:
        for idx in range(limit, 0, -1):
            if text[idx - 1] in split_marks:
                return idx

    # Fall back to whitespace
    for idx in range(limit, 0, -1):
        if text[idx - 1].isspace():
            return idx

    return -1


def _split_long_text(text: str, max_length: int, punctuation_marks: str) -> List[str]:
    """
    Split long text into chunks that respect sentence boundaries.

    Args:
        text: Text to split
        max_length: Maximum characters per segment
        punctuation_marks: String of punctuation marks for splitting

    Returns:
        List of text segments (all <= max_length if possible)
    """
    if max_length <= 0 or len(text) <= max_length:
        return [text]

    # Build split marks from punctuation
    split_marks = set(punctuation_marks)

    chunks: List[str] = []
    remainder = text.strip()

    while remainder:
        if len(remainder) <= max_length:
            chunks.append(remainder)
            break

        # Find best split point
        split_idx = _find_split_index(remainder, max_length, punctuation_marks)
        if split_idx == -1:
            # No good split point found, force split at max_length
            split_idx = max_length

        chunk = remainder[:split_idx].strip()
        if chunk:
            chunks.append(chunk)

        remainder = remainder[split_idx:].lstrip()

    return chunks


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
        self.batch_duration_ms = int(minimax_settings.get("batch_duration_ms", 2000))

        # Time-based text segmentation (MoFA Flow approach)
        # Convert max duration (seconds) to character count
        # Estimate: ~250-300 Chinese chars/minute = ~4-5 chars/second
        # For 10 seconds: ~40-50 characters
        max_segment_duration = float(minimax_settings.get("max_segment_duration", 10.0))  # seconds
        chars_per_second = float(minimax_settings.get("tts_chars_per_second", 4.5))  # Conservative for Chinese
        self.max_segment_chars = int(max_segment_duration * chars_per_second)

        logger.info(
            f"文本分段配置: max_duration={max_segment_duration}s, "
            f"chars_per_second={chars_per_second}, "
            f"max_length={self.max_segment_chars} chars"
        )

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
                batch_duration_ms=int(override.get("batch_duration_ms", self.batch_duration_ms)),
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
                batch_duration_ms=int(override.get("batch_duration_ms", self.batch_duration_ms)),
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

    def generate_multi(self, dialogue: List[Dict], participants_config: List[Dict], output_path: str) -> str:
        """
        Generate multi-person podcast audio from dialogue JSON (for debate/conference).

        Args:
            dialogue: List of dialogue entries [{"participant": "llm1", "content": "..."},...]
            participants_config: List of participant configs [{"id": "llm1", "voice_id": "...", "role": "..."},...]
            output_path: Where to save the generated MP3

        Returns:
            Path to the generated audio file
        """
        logger.info("MiniMax 多人播客生成开始 (%d 参与者, %d 对话条目)", len(participants_config), len(dialogue))

        # Build voice configs for each participant
        participant_voices = {}
        for p_config in participants_config:
            participant_id = p_config['id']
            voice_id = p_config.get('voice_id')

            if not voice_id:
                logger.warning("参与者 %s 未配置 voice_id，跳过", participant_id)
                continue

            # Create MiniMax voice config
            config = MiniMaxVoiceConfig(
                api_key=self.api_key,
                model=self.model,
                voice_id=voice_id,
                speed=1.0,
                volume=1.0,
                pitch=0,
                sample_rate=self.sample_rate,
                audio_bitrate=self.audio_bitrate,
                audio_channel=self.audio_channel,
                enable_english_normalization=self.enable_english_normalization,
                batch_duration_ms=self.batch_duration_ms,
            )
            participant_voices[participant_id] = config

        # Split long dialogue entries
        segments = []
        for entry in dialogue:
            participant_id = entry['participant']
            content = entry['content']

            if participant_id not in participant_voices:
                logger.warning("跳过未配置语音的参与者 %s", participant_id)
                continue

            # Split long content into smaller segments
            parts = _split_long_text(content, self.max_segment_chars, self.punctuation_marks)
            for part in parts:
                if part:
                    segments.append((participant_id, part))

        logger.info("共 %d 个语音片段", len(segments))

        if not segments:
            raise ValueError("未找到有效的对话内容")

        try:
            audio_segments = asyncio.run(self._generate_multi_segments(segments, participant_voices))
        except Exception as exc:
            logger.exception("调用 MiniMax 生成多人音频失败: %s", exc)
            raise

        if not audio_segments:
            raise ValueError("MiniMax 未生成任何音频片段")

        # Concatenate with silence between speaker changes
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
        logger.info("MiniMax 多人播客生成完成，输出路径: %s", output_path)

        return output_path

    async def _generate_multi_segments(
        self,
        segments: List[Tuple[str, str]],
        participant_voices: Dict[str, MiniMaxVoiceConfig]
    ) -> List[Tuple[str, AudioSegment]]:
        """Generate audio for multi-person dialogue segments."""
        results: List[Tuple[str, AudioSegment]] = []

        for index, (participant_id, text) in enumerate(segments, start=1):
            config = participant_voices.get(participant_id)
            if not config:
                logger.warning("跳过未配置语音的参与者 %s", participant_id)
                continue

            logger.info(
                "MiniMax 生成片段 %s/%s (%s): '%s...' (len=%d)",
                index, len(segments), participant_id, text[:30], len(text)
            )

            def client_logger(message: str, *, _pid=participant_id, _index=index):
                logger.debug("[MiniMax][%s #%s] %s", _pid, _index, message)

            # Get float32 audio array from MiniMax
            sample_rate, audio_float32 = await synthesize_to_pcm(config, text, logger=client_logger)

            # Convert float32 [-1, 1] back to int16 for pydub
            audio_int16 = (audio_float32 * 32767).astype(np.int16)

            # Create AudioSegment from int16 array
            segment_audio = AudioSegment(
                data=audio_int16.tobytes(),
                sample_width=2,  # 16-bit
                frame_rate=sample_rate,
                channels=config.audio_channel,
            )
            results.append((participant_id, segment_audio))

        return results

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
        """
        Generate audio for all text segments.

        Processes float32 numpy arrays from MiniMax and converts to AudioSegment.
        """
        results: List[Tuple[str, AudioSegment]] = []

        for index, (speaker, text) in enumerate(segments, start=1):
            config = self.voice_configs.get(speaker)
            if not config:
                logger.warning("跳过未配置语音的角色 %s", speaker)
                continue

            logger.info("MiniMax 生成片段 %s/%s (%s): '%s...' (len=%d)", index, len(segments), speaker, text[:30], len(text))

            def client_logger(message: str, *, _speaker=speaker, _index=index):
                logger.debug("[MiniMax][%s #%s] %s", _speaker, _index, message)

            # Get float32 audio array from MiniMax
            sample_rate, audio_float32 = await synthesize_to_pcm(config, text, logger=client_logger)

            # Convert float32 [-1, 1] back to int16 for pydub
            audio_int16 = (audio_float32 * 32767).astype(np.int16)

            # Create AudioSegment from int16 array
            segment_audio = AudioSegment(
                data=audio_int16.tobytes(),
                sample_width=2,  # 16-bit
                frame_rate=sample_rate,
                channels=config.audio_channel,
            )
            results.append((speaker, segment_audio))

        return results
