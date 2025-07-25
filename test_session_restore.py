"""
SQLiteSessionへの履歴復元をテストするスクリプト
"""
import asyncio
from agents import Agent, Runner, SQLiteSession


async def test_session_restoration():
    """セッションへのメッセージ復元をテスト"""
    
    # 新しいインメモリセッションを作成
    session = SQLiteSession("test-session")
    
    # ダミーエージェントを作成
    agent = Agent(
        name="Test Agent",
        instructions="You are a test agent"
    )
    
    # セッションで会話を実行
    print("=== 初回の会話 ===")
    result1 = await Runner.run(agent, "Hello, how are you?", session=session)
    print(f"User: Hello, how are you?")
    print(f"Agent: {result1.final_output}")
    
    result2 = await Runner.run(agent, "What's your name?", session=session)
    print(f"\nUser: What's your name?")
    print(f"Agent: {result2.final_output}")
    
    # セッションの内容を確認
    print("\n=== セッションの内容を確認 ===")
    items = await session.get_items()
    print(f"セッション内のアイテム数: {len(items)}")
    
    for i, item in enumerate(items):
        print(f"\nItem {i}: {type(item).__name__}")
        if isinstance(item, dict):
            print(f"  Keys: {list(item.keys())}")
            if 'role' in item:
                print(f"  Role: {item['role']}")
            if 'content' in item:
                print(f"  Content: {item['content'][:100]}...")
            if 'type' in item:
                print(f"  Type: {item['type']}")
    
    # 新しいセッションを作成して、履歴を手動で復元する試み
    print("\n=== 新しいセッションに履歴を復元 ===")
    new_session = SQLiteSession("restored-session")
    
    # 既存のアイテムをコピーしようとする
    # 注: これは実際のAPIの制限により動作しない可能性があります
    try:
        await new_session.add_items(items)
        print("履歴の復元に成功しました")
    except Exception as e:
        print(f"履歴の復元に失敗: {e}")
        print("代替方法: 会話履歴をコンテキストとして使用することを推奨")
    
    # 復元されたセッションでの会話
    result3 = await Runner.run(agent, "Do you remember what we talked about?", session=new_session)
    print(f"\nUser: Do you remember what we talked about?")
    print(f"Agent: {result3.final_output}")


if __name__ == "__main__":
    asyncio.run(test_session_restoration())