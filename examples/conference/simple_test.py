#!/usr/bin/env python3
"""
简单测试脚本 - 不用TUI，直接发送消息测试conference-controller
"""
import time
import json
import pyarrow as pa
from dora import Node

def main():
    print("[simple-test] Connecting to dataflow as 'debate-monitor'...")
    node = Node("debate-monitor")
    print("[simple-test] ✓ Connected!")

    print("\n[simple-test] Waiting 2 seconds for dataflow to stabilize...")
    time.sleep(2)

    # 发送一个控制消息给judge，启动对话（使用正确的JSON格式）
    initial_prompt = "请开始辩论：人工智能是否会取代人类？请简短回答（50字以内）。"

    print(f"\n[simple-test] Sending initial prompt to judge: {initial_prompt}")
    json_content = json.dumps({"prompt": initial_prompt})
    print(f"[simple-test] JSON: {json_content}")
    node.send_output("control", pa.array([json_content]))

    print("\n[simple-test] Listening for events (90 seconds)...")
    start_time = time.time()
    event_count = 0

    while time.time() - start_time < 90:
        event = node.next(timeout=0.5)

        if event is None:
            continue

        event_count += 1
        event_type = event.get("type")

        if event_type == "STOP":
            print("\n[simple-test] Received STOP signal")
            break

        if event_type == "INPUT":
            input_id = event.get("id", "unknown")
            value = event.get("value")

            # 提取文本内容
            if value is not None and len(value) > 0:
                content = str(value[0]) if hasattr(value[0], '__str__') else str(value)
                content_preview = content[:200] + "..." if len(content) > 200 else content
                print(f"\n[Event #{event_count}] {input_id}")
                print(f"  Content: {content_preview}")
            else:
                print(f"\n[Event #{event_count}] {input_id} (empty)")

        elif event_type == "ERROR":
            error_msg = event.get("error", "unknown error")
            node_id = event.get("id", "unknown")
            print(f"\n[Event #{event_count}] ERROR from {node_id}")
            print(f"  Error: {str(error_msg)[:300]}")
        else:
            print(f"\n[Event #{event_count}] Type: {event_type}, Data: {str(event)[:200]}")

    print(f"\n[simple-test] Test complete. Received {event_count} events.")
    print("[simple-test] Check if LLMs responded in order: llm1 → llm2 → judge")

if __name__ == "__main__":
    main()
