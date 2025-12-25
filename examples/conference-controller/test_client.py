#!/usr/bin/env python3
"""WebSocket test client for conference controller"""
import asyncio
import json
import websockets

async def send_message(port, role, message):
    uri = f"ws://localhost:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            payload = {
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
            print(f"[{role}] Sending: {message}")
            await websocket.send(json.dumps(payload))

            response = await websocket.recv()
            print(f"[{role}] Response: {response}")
    except Exception as e:
        print(f"[{role}] Error: {e}")

async def test_conference():
    """Test the conference controller with a simple exchange"""

    # Wait for system to be ready
    await asyncio.sleep(2)

    # Judge initiates
    print("\n=== Judge speaks ===")
    await send_message(8001, "Judge", "请陈述案情摘要")
    await asyncio.sleep(3)

    # Defense responds
    print("\n=== Defense speaks ===")
    await send_message(8002, "Defense", "我方认为被告无罪")
    await asyncio.sleep(3)

    # Prosecution responds
    print("\n=== Prosecution speaks ===")
    await send_message(8003, "Prosecution", "证据充分，被告有罪")
    await asyncio.sleep(2)

    print("\n=== Test complete ===")

if __name__ == "__main__":
    print("Conference Controller Test Client")
    print("==================================")
    asyncio.run(test_conference())
