"""
RedisSessionのテスト
"""
import asyncio
import uuid
from redis_session import RedisSession, create_redis_session


async def test_basic_operations():
    """基本的な操作のテスト"""
    print("=== RedisSession基本操作テスト ===\n")
    
    # テスト用のセッションID
    session_id = f"test-{uuid.uuid4()}"
    print(f"テストセッションID: {session_id}")
    
    # セッションを作成
    session = await create_redis_session(session_id)
    
    # 1. 空のセッションを確認
    print("\n1. 空のセッションを確認")
    items = await session.get_items()
    print(f"   アイテム数: {len(items)}")
    assert len(items) == 0, "新規セッションは空であるべき"
    
    # 2. アイテムを追加
    print("\n2. アイテムを追加")
    test_items = [
        {"role": "user", "content": "こんにちは"},
        {"role": "assistant", "content": [{"type": "output_text", "text": "こんにちは！お元気ですか？"}]}
    ]
    await session.add_items(test_items)
    print("   2つのアイテムを追加しました")
    
    # 3. アイテムを取得
    print("\n3. アイテムを取得")
    items = await session.get_items()
    print(f"   取得したアイテム数: {len(items)}")
    assert len(items) == 2, "2つのアイテムがあるべき"
    
    # 4. 制限付きで取得
    print("\n4. 制限付きで取得")
    limited_items = await session.get_items(limit=1)
    print(f"   制限付き取得数: {len(limited_items)}")
    assert len(limited_items) == 1, "1つのアイテムのみ取得されるべき"
    
    # 5. アイテムをポップ
    print("\n5. 最新アイテムをポップ")
    popped = await session.pop_item()
    print(f"   ポップしたアイテム: {popped['role']}")
    items = await session.get_items()
    print(f"   残りのアイテム数: {len(items)}")
    assert len(items) == 1, "1つのアイテムが残るべき"
    
    # 6. セッション情報を取得
    print("\n6. セッション情報を取得")
    info = await session.get_session_info()
    print(f"   セッションID: {info['session_id']}")
    print(f"   アイテム数: {info['item_count']}")
    print(f"   TTL: {info['ttl_seconds']}秒")
    
    # 7. セッションをクリア
    print("\n7. セッションをクリア")
    await session.clear_session()
    items = await session.get_items()
    print(f"   クリア後のアイテム数: {len(items)}")
    assert len(items) == 0, "セッションは空になるべき"
    
    # クリーンアップ
    await session.close()
    print("\n✅ 基本操作テスト完了")


async def test_session_persistence():
    """セッションの永続性テスト"""
    print("\n\n=== セッション永続性テスト ===\n")
    
    session_id = f"persist-{uuid.uuid4()}"
    print(f"テストセッションID: {session_id}")
    
    # 1. セッションにデータを保存
    print("\n1. セッションにデータを保存")
    session1 = await create_redis_session(session_id)
    
    test_conversation = [
        {"role": "user", "content": "Pythonについて教えて"},
        {"role": "assistant", "content": [{"type": "output_text", "text": "Pythonは汎用プログラミング言語です"}]},
        {"role": "user", "content": "特徴は？"},
        {"role": "assistant", "content": [{"type": "output_text", "text": "読みやすく、多様なライブラリがあります"}]}
    ]
    
    await session1.add_items(test_conversation)
    print(f"   {len(test_conversation)}個のメッセージを保存")
    await session1.close()
    
    # 2. 別のインスタンスで復元
    print("\n2. 別のインスタンスで復元")
    session2 = await create_redis_session(session_id)
    
    restored_items = await session2.get_items()
    print(f"   復元したアイテム数: {len(restored_items)}")
    assert len(restored_items) == len(test_conversation), "すべてのアイテムが復元されるべき"
    
    # 内容を確認
    print("\n   復元した会話:")
    for i, item in enumerate(restored_items):
        if item["role"] == "user":
            print(f"   [{i+1}] User: {item['content']}")
        else:
            content = item["content"][0]["text"] if isinstance(item["content"], list) else item["content"]
            print(f"   [{i+1}] Assistant: {content}")
    
    # クリーンアップ
    await session2.clear_session()
    await session2.close()
    
    print("\n✅ 永続性テスト完了")


async def test_concurrent_access():
    """並行アクセステスト"""
    print("\n\n=== 並行アクセステスト ===\n")
    
    session_id = f"concurrent-{uuid.uuid4()}"
    print(f"テストセッションID: {session_id}")
    
    async def add_messages(session_num: int, count: int):
        """指定された数のメッセージを追加"""
        session = await create_redis_session(session_id)
        
        for i in range(count):
            await session.add_items([
                {"role": "user", "content": f"Session{session_num} - Message{i+1}"}
            ])
            await asyncio.sleep(0.01)  # 少し待機
        
        await session.close()
        return session_num
    
    # 3つのセッションから同時にアクセス
    print("3つのセッションから同時にメッセージを追加...")
    tasks = [
        add_messages(1, 3),
        add_messages(2, 3),
        add_messages(3, 3)
    ]
    
    results = await asyncio.gather(*tasks)
    print(f"完了したセッション: {results}")
    
    # 結果を確認
    session = await create_redis_session(session_id)
    items = await session.get_items()
    print(f"\n合計メッセージ数: {len(items)}")
    assert len(items) == 9, "9つのメッセージがあるべき"
    
    # クリーンアップ
    await session.clear_session()
    await session.close()
    
    print("\n✅ 並行アクセステスト完了")


async def main():
    """すべてのテストを実行"""
    print("RedisSessionテストを開始します...\n")
    
    try:
        # 基本操作テスト
        await test_basic_operations()
        
        # 永続性テスト
        await test_session_persistence()
        
        # 並行アクセステスト
        await test_concurrent_access()
        
        print("\n\n🎉 すべてのテストが成功しました！")
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())