#!/usr/bin/env python3
"""
测试Debate生成功能
"""
import requests
import time
import json
import sys

BASE_URL = "https://test.mofa.fm/api"

# JWT token (通过Django shell生成)
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1ODEyMTU1LCJpYXQiOjE3NjU4MDg1NTUsImp0aSI6IjZhMzQzZGNjNGIwYjRhMGQ5M2M1ZTk3Y2M4Y2U5Mzk3IiwidXNlcl9pZCI6MX0.cY9qpwZP_SSi0QNx6PacbDWbHFNcBvAK5HzU2Oiv4Fk"

def get_auth_headers():
    """获取认证headers"""
    return {"Authorization": f"Bearer {JWT_TOKEN}"}

def test_debate_generation():
    """测试debate生成"""
    # Step 1: 获取shows列表，找一个测试用的show
    print("🔍 Fetching shows...")
    response = requests.get(f"{BASE_URL}/podcasts/shows/")
    if response.status_code != 200:
        print(f"❌ Failed to fetch shows: {response.status_code}")
        print(response.text)
        return False

    shows = response.json()
    if not shows or 'results' not in shows or len(shows['results']) == 0:
        print("❌ No shows found. Please create a show first.")
        return False

    show_id = shows['results'][0]['id']
    print(f"✅ Using show ID: {show_id}")

    # Step 2: 创建debate episode
    print("\n🎭 Creating debate episode...")
    debate_data = {
        "show_id": show_id,
        "title": "测试：AI是否会取代程序员",
        "topic": "AI是否会取代程序员？这是一个关于人工智能和程序员职业未来的辩论。",
        "mode": "debate",
        "rounds": 2  # 减少轮数以加快测试
    }

    # 使用JWT认证
    response = requests.post(
        f"{BASE_URL}/podcasts/episodes/generate-debate/",
        json=debate_data,
        headers=get_auth_headers()
    )

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text[:500]}")

    if response.status_code != 202:
        print(f"❌ Failed to create debate: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    episode_id = result['episode_id']
    print(f"✅ Debate generation started! Episode ID: {episode_id}")

    # Step 3: 轮询检查episode状态
    print(f"\n⏳ Waiting for debate generation...")
    max_wait = 120  # 最多等待2分钟
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(5)
        elapsed += 5

        # 查询episode详情
        response = requests.get(f"{BASE_URL}/podcasts/episodes/{episode_id}/")
        if response.status_code != 200:
            continue

        episode = response.json()
        status = episode.get('status')
        print(f"  [{elapsed}s] Status: {status}")

        if status == 'published':
            print("\n✅ Debate generation completed!")

            # 显示结果
            print(f"\n📝 Title: {episode.get('title')}")
            print(f"Mode: {episode.get('mode')}")

            # 显示对话记录
            dialogue = episode.get('dialogue')
            if dialogue:
                print(f"\n💬 Dialogue ({len(dialogue)} entries):")
                for i, entry in enumerate(dialogue[:6], 1):  # 只显示前6条
                    participant = entry.get('participant')
                    content = entry.get('content', '')[:100]
                    print(f"  {i}. [{participant}] {content}...")

            # 显示脚本
            script = episode.get('script', '')
            if script:
                print(f"\n📜 Script preview:")
                print(script[:500] + "...")

            return True

        if status == 'failed':
            print(f"\n❌ Debate generation failed!")
            return False

    print(f"\n⏱️ Timeout after {max_wait}s")
    return False

if __name__ == '__main__':
    print("=" * 60)
    print("🎙️  MoFA-FM Debate Generation Test")
    print("=" * 60)

    success = test_debate_generation()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Tests failed")
        sys.exit(1)
