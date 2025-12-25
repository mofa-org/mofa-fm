#!/usr/bin/env python3
"""独立WebSocket服务器 - 接收消息并写入文件供Dora节点读取"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
import websockets

async def handle_client(websocket, port):
    """处理WebSocket客户端连接"""
    msg_dir = Path(f"/tmp/dora-ws-{port}")
    msg_dir.mkdir(exist_ok=True)

    client_addr = websocket.remote_address
    print(f"[WS-{port}] Connection from {client_addr}")

    try:
        async for message in websocket:
            print(f"[WS-{port}] Received: {message[:50]}...")

            # 解析OpenAI格式
            try:
                data = json.loads(message)
                if "messages" in data and isinstance(data["messages"], list):
                    if data["messages"]:
                        content = data["messages"][-1].get("content", "")

                        # 写入消息文件
                        timestamp = int(time.time() * 1000000)
                        msg_file = msg_dir / f"msg_{timestamp}.txt"
                        msg_file.write_text(content)

                        print(f"[WS-{port}] ✓ Wrote to {msg_file.name}")

                        # 发送确认
                        await websocket.send(json.dumps({"status": "ok"}))
            except Exception as e:
                print(f"[WS-{port}] Error: {e}")
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))

    except websockets.exceptions.ConnectionClosed:
        print(f"[WS-{port}] Connection closed")

async def start_server(port):
    """启动WebSocket服务器"""
    print(f"[WS-{port}] Starting WebSocket server")
    print(f"[WS-{port}] Messages will be written to /tmp/dora-ws-{port}/")

    async with websockets.serve(
        lambda ws: handle_client(ws, port),
        "0.0.0.0",
        port
    ):
        print(f"[WS-{port}] ✓ Listening on ws://0.0.0.0:{port}")
        await asyncio.Future()  # Run forever

async def main():
    """启动所有WebSocket服务器"""
    ports = [8001, 8002, 8003]

    print("=" * 50)
    print("WebSocket Servers for Dora Conference Controller")
    print("=" * 50)

    servers = [start_server(port) for port in ports]
    await asyncio.gather(*servers)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
