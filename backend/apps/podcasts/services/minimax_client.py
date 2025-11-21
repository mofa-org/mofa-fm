"""
MiniMax TTS WebSocket helper for podcast audio generation.

This client mirrors the behaviour used in the MoFA `podcast-generator`
flow (see mofa/flows/podcast-generator) and provides a thin async wrapper
that can be consumed by our Celery tasks.
"""

from __future__ import annotations

import asyncio
import json
import ssl
from dataclasses import dataclass
from typing import AsyncGenerator, Callable, Optional, Tuple

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

    async def stream_text(self, text: str) -> AsyncGenerator[Tuple[int, bytes], None]:
        """Stream PCM audio chunks for the given text."""
        if not self._ws:
            raise MiniMaxError("MiniMax WebSocket 未初始化")

        await self._ws.send(json.dumps({"event": "task_continue", "text": text}))
        self.logger(f"MiniMax 开始生成语音 (长度 {len(text)})")

        while True:
            response = json.loads(await self._ws.recv())

            # Audio fragments
            if "data" in response and "audio" in response["data"]:
                audio_hex = response["data"]["audio"]
                if audio_hex:
                    yield self.config.sample_rate, bytes.fromhex(audio_hex)

            # Completed
            if response.get("is_final"):
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
) -> Tuple[int, bytes]:
    """
    Convenience helper: synthesize `text` and return raw PCM bytes with sample rate.
    """
    config.validate()

    chunks: list[bytes] = []
    async with MiniMaxWebSocketClient(config, logger=logger) as client:
        async for sample_rate, chunk in client.stream_text(text):
            chunks.append(chunk)

    if not chunks:
        raise MiniMaxError("MiniMax 未返回任何音频片段")

    return config.sample_rate, b"".join(chunks)


def synthesize_text(
    config: MiniMaxVoiceConfig,
    text: str,
    logger: Optional[Callable[[str], None]] = None,
) -> Tuple[int, bytes]:
    """
    Synchronous wrapper around `synthesize_to_pcm`.
    """

    return asyncio.run(synthesize_to_pcm(config, text, logger=logger))
