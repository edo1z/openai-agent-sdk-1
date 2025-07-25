"""
Langfuseから履歴を復元してインメモリセッションに追加するテスト
"""
import asyncio
from session_builder import SessionBuilder
from agents import Agent, Runner


async def test_restore_from_langfuse():
    """既存のセッションIDから履歴を復元してテスト"""
    
    # テスト用のセッションID（実際のセッションIDに置き換えてください）
    session_id = input("復元するセッションIDを入力してください: ").strip()
    
    if not session_id:
        print("セッションIDが入力されませんでした")
        return
    
    print(f"\nセッション {session_id} の履歴を復元中...")
    
    # Langfuseから履歴を復元
    session = await SessionBuilder.rebuild_from_langfuse(session_id)
    
    # 復元されたセッションの内容を確認
    print("\n=== 復元されたセッションの内容 ===")
    items = await session.get_items()
    print(f"アイテム数: {len(items)}")
    
    for i, item in enumerate(items[-6:]):  # 最後の3往復を表示
        if isinstance(item, dict):
            role = item.get('role', 'unknown')
            if role == 'user':
                print(f"\nユーザー: {item['content']}")
            elif role == 'assistant':
                # アシスタントのcontentは配列形式
                if isinstance(item['content'], list) and item['content']:
                    text = item['content'][0].get('text', '')
                    print(f"アシスタント: {text}")
    
    # 復元されたセッションで新しい会話を続ける
    print("\n\n=== 会話を続行 ===")
    
    # ダミーエージェントを作成
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful assistant. Use the conversation history in the session to provide contextual responses."
    )
    
    # 新しい質問をする
    user_input = input("\n新しい質問を入力してください: ").strip()
    
    if user_input:
        result = await Runner.run(agent, user_input, session=session)
        print(f"\nアシスタントの回答: {result.final_output}")
        
        # セッションが更新されたことを確認
        print("\n=== 更新後のセッション ===")
        items = await session.get_items()
        print(f"アイテム数: {len(items)}")


if __name__ == "__main__":
    asyncio.run(test_restore_from_langfuse())