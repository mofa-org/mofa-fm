import asyncio
import json

import websockets


async def run():
    uri = "ws://localhost:8123"
    print("连接到", uri)
    async with websockets.connect(uri) as ws:
        print("发送 session.update")
        await ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text"],
                        "instructions": "请用中文回答，并保持回复精简。",
                        "voice": "alloy",
                        "model": "gpt-4o",
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {
                            "model": "whisper",
                            "language": "zh",
                        },
                        "tools": [],
                        "tool_choice": "auto",
                        "temperature": 0.8,
                        "turn_detection": None,
                        "max_response_output_tokens": 150,
                    },
                }
            )
        )
        response = json.loads(await ws.recv())
        print("收到", response["type"])

        print("发送 response.create")
        await ws.send(
            json.dumps(
                {
                    "type": "response.create",
                    "response": {
                        "modalities": ["text"],
                        "instructions": "简短欢迎一下来到浏览器语音助手的测试环境。",
                    },
                }
            )
        )

        for i in range(20):
            message = json.loads(await ws.recv())
            print(f"[{i}] {message['type']}")
            if message["type"] == "audio.delta":
                print("   音频字节数:", len(message.get("delta", {}).get("audio", [])))
            if message["type"] == "text.delta":
                print("   文本片段:", message.get("delta", {}).get("text", ""))
            if message["type"] == "response.done":
                break


if __name__ == "__main__":
    asyncio.run(run())
