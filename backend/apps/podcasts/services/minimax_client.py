"""
MiniMax TTS WebSocket helper for podcast audio generation.

This client mirrors the behaviour used in the MoFA `podcast-generator`
flow (see mofa/flows/podcast-generator) and provides a thin async wrapper
that can be consumed by our Celery tasks.

Updated to match MoFA Flow implementation exactly.
"""

from __future__ import annotations

import asyncio
import json
import ssl
from dataclasses import dataclass
from typing import AsyncGenerator, Callable, Optional, Tuple

import numpy as np
import websockets


class MiniMaxError(RuntimeError):
    """Raised when the MiniMax API returns an unexpected response."""


@dataclass
class MiniMaxVoiceConfig:
    """Configuration for a single MiniMax TTS voice."""

    api_key: str
    model: str = "speech-2.5-hd-preview"
    voice_id: str = ""
    speed: float = 1.0
    volume: float = 1.0
    pitch: int = 0
    sample_rate: int = 32000
    audio_bitrate: int = 128000
    audio_channel: int = 1
    enable_english_normalization: bool = True
    batch_duration_ms: int = 2000  # Audio batching to prevent shared memory issues

    def validate(self) -> None:
        if not self.api_key:
            raise MiniMaxError("MINIMAX_API_KEY 未配置，无法生成语音")

        if not self.voice_id:
            raise MiniMaxError("MiniMax 语音 ID 未设置，请检查配置")

        if self.sample_rate not in {8000, 16000, 24000, 32000}:
            raise MiniMaxError(f"不支持的采样率: {self.sample_rate}")

        if not (0.5 <= self.speed <= 2.0):
            raise MiniMaxError(f"语速需在 0.5~2.0 范围内，当前 {self.speed}")

        if not (0 <= self.volume <= 2.0):
            raise MiniMaxError(f"音量需在 0~2.0 范围内，当前 {self.volume}")

        if not (-12 <= self.pitch <= 12):
            raise MiniMaxError(f"音调需在 -12~12 范围内，当前 {self.pitch}")

        if self.audio_channel not in {1, 2}:
            raise MiniMaxError(f"仅支持单声道或双声道 (1 or 2)，当前 {self.audio_channel}")


class MiniMaxWebSocketClient:
    """
    Lightweight async client for MiniMax streaming TTS.

    Usage:
        async with MiniMaxWebSocketClient(config) as client:
            async for sr, chunk in client.stream_text("..."):
                ...
    """

    def __init__(
        self,
        config: MiniMaxVoiceConfig,
        logger: Optional[Callable[[str], None]] = None,
    ):
        self.config = config
        self.logger = logger or (lambda message: None)
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False

    async def __aenter__(self) -> "MiniMaxWebSocketClient":
        await self.connect()
        await self.start_task()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def connect(self) -> None:
        """Establish the WebSocket connection."""
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            # MiniMax WebSocket API uses Bearer token in Authorization header
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            self._ws = await websockets.connect(
                "wss://api.minimax.io/ws/v1/t2a_v2",
                additional_headers=headers,
                ssl=ssl_context,
            )

            response = json.loads(await self._ws.recv())
            if response.get("event") != "connected_success":
                raise MiniMaxError(f"MiniMax 握手失败: {response}")

            self._connected = True
            self.logger("MiniMax 已建立连接")
        except Exception as exc:  # pragma: no cover - network errors are runtime issues
            raise MiniMaxError(f"MiniMax 连接失败: {exc}") from exc

    async def start_task(self) -> None:
        """Send task_start command and wait for acknowledgement."""
        if not self._connected or not self._ws:
            raise MiniMaxError("MiniMax 连接尚未建立")

        start_payload = {
            "event": "task_start",
            "model": self.config.model,
            "voice_setting": {
                "voice_id": self.config.voice_id,
                "speed": self.config.speed,
                "vol": self.config.volume,
                "pitch": self.config.pitch,
                "english_normalization": self.config.enable_english_normalization,
            },
            "audio_setting": {
                "sample_rate": self.config.sample_rate,
                "bitrate": self.config.audio_bitrate,
                "format": "pcm",
                "channel": self.config.audio_channel,
            },
        }

        await self._ws.send(json.dumps(start_payload))
        response = json.loads(await self._ws.recv())
        if response.get("event") != "task_started":
            raise MiniMaxError(f"MiniMax 未能启动任务: {response}")
        self.logger("MiniMax 任务启动成功")

    async def stream_text(self, text: str) -> AsyncGenerator[Tuple[int, np.ndarray], None]:
        """
        Stream PCM audio chunks for the given text.

        Uses batching logic from MoFA Flow to prevent shared memory issues.
        Yields float32 numpy arrays normalized to [-1, 1] range.
        """
        if not self._ws:
            raise MiniMaxError("MiniMax WebSocket 未初始化")

        await self._ws.send(json.dumps({"event": "task_continue", "text": text}))
        self.logger(f"MiniMax 开始生成语音 (长度 {len(text)})")

        # Batching configuration (from MoFA Flow)
        batch_duration_threshold = self.config.batch_duration_ms / 1000.0  # Convert ms to seconds
        chunk_buffer = []
        batch_accumulated_duration = 0.0
        chunk_counter = 0

        while True:
            response = json.loads(await self._ws.recv())

            # Audio fragments
            if "data" in response and "audio" in response["data"]:
                audio_hex = response["data"]["audio"]
                if audio_hex:
                    chunk_counter += 1
                    audio_bytes = bytes.fromhex(audio_hex)

                    # Convert PCM bytes to numpy float32 array (MoFA Flow approach)
                    # PCM format: 16-bit signed integers, normalize to [-1, 1]
                    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0

                    fragment_duration = len(audio_float32) / self.config.sample_rate

                    # Add to buffer
                    chunk_buffer.append(audio_float32)
                    batch_accumulated_duration += fragment_duration

                    # Send batch when accumulated duration exceeds threshold
                    if batch_accumulated_duration >= batch_duration_threshold:
                        batched_audio = np.concatenate(chunk_buffer)
                        self.logger(f"发送批次音频: {len(batched_audio)} 采样点, {batch_accumulated_duration:.2f}秒")
                        yield self.config.sample_rate, batched_audio

                        # Reset buffer
                        chunk_buffer = []
                        batch_accumulated_duration = 0.0

            # Completed
            if response.get("is_final"):
                # Send remaining chunks in buffer
                if chunk_buffer:
                    batched_audio = np.concatenate(chunk_buffer)
                    self.logger(f"发送最后批次音频: {len(batched_audio)} 采样点, {batch_accumulated_duration:.2f}秒")
                    yield self.config.sample_rate, batched_audio

                self.logger(f"语音生成完成，共处理 {chunk_counter} 个原始片段")
                break

    async def close(self) -> None:
        """Finish the task and close the connection."""
        if not self._ws:
            return
        try:
            await self._ws.send(json.dumps({"event": "task_finish"}))
        finally:
            await self._ws.close()
            self._ws = None
            self._connected = False
            self.logger("MiniMax 连接已关闭")


async def synthesize_to_pcm(
    config: MiniMaxVoiceConfig,
    text: str,
    logger: Optional[Callable[[str], None]] = None,
) -> Tuple[int, np.ndarray]:
    """
    Convenience helper: synthesize `text` and return float32 numpy array with sample rate.

    Returns:
        Tuple of (sample_rate, audio_float32_array)
        Audio is normalized to [-1, 1] range as float32.
    """
    config.validate()

    chunks: list[np.ndarray] = []
    async with MiniMaxWebSocketClient(config, logger=logger) as client:
        async for sample_rate, chunk in client.stream_text(text):
            chunks.append(chunk)

    if not chunks:
        raise MiniMaxError("MiniMax 未返回任何音频片段")

    # Concatenate all batched audio chunks
    final_audio = np.concatenate(chunks)
    return config.sample_rate, final_audio


def synthesize_text(
    config: MiniMaxVoiceConfig,
    text: str,
    logger: Optional[Callable[[str], None]] = None,
) -> Tuple[int, np.ndarray]:
    """
    Synchronous wrapper around `synthesize_to_pcm`.

    Returns:
        Tuple of (sample_rate, audio_float32_array)
    """
    return asyncio.run(synthesize_to_pcm(config, text, logger=logger))
