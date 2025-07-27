#!/usr/bin/env python3
"""
会議システムのテストスクリプト
"""
import asyncio
import os
from redis_session import create_redis_session

async def test_conference():
    """会議システムをテスト"""
    # 新規セッションを作成
    session_id = "test-conference-session"
    session = await create_redis_session(session_id, restore_existing=False)
    
    # 過去の会話履歴を追加（ユーザーの名前を含む）
    await session.add_items([
        {"role": "user", "content": "こんにちは、私は田中太郎です。"},
        {"role": "assistant", "content": "【司会者】\nこんにちは、田中太郎様。会議にご参加いただきありがとうございます。"}
    ])
    
    # セッション情報を確認
    info = await session.get_session_info()
    print(f"セッションID: {session_id}")
    print(f"保存されたアイテム数: {info['item_count']}")
    print(f"セッションは存在する: {info['exists']}")
    
    # 会話履歴を取得
    items = await session.get_items()
    print(f"\n会話履歴:")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['role']}: {item['content'][:50]}...")
    
    print(f"\nこのセッションIDを使用してmain_conference.pyを実行してください: {session_id}")
    
    await session.close()

if __name__ == "__main__":
    asyncio.run(test_conference())