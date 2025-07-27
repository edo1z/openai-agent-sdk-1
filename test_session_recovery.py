"""
セッション復元のテストと問題の特定
"""
import asyncio
import os
from agents import Agent, Runner, SQLiteSession
from session_builder import SessionBuilder
from advanced_session_builder import AdvancedSessionBuilder
from conversation_history import ConversationHistoryLoader


async def test_session_recovery():
    """セッション復元の詳細なテスト"""
    
    print("=== ステップ1: 新しいセッションで会話を開始 ===")
    
    # 新しいセッションを作成
    session_id = "test-recovery-session"
    session1 = SQLiteSession(session_id)
    
    # テスト用エージェント
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful assistant. Remember previous conversations."
    )
    
    # 最初の会話
    result1 = await Runner.run(agent, "私の好きな果物を5つリストアップしてください：りんご、みかん、ぶどう、メロン、いちご", session=session1)
    print(f"\nUser: 私の好きな果物を5つリストアップしてください")
    print(f"Assistant: {result1.final_output[:200]}...")
    
    # セッション内容を確認
    print("\n=== セッション1の内容 ===")
    items1 = await session1.get_items()
    print(f"アイテム数: {len(items1)}")
    for i, item in enumerate(items1):
        if isinstance(item, dict) and 'role' in item:
            print(f"  {i}: {item['role']} - {str(item.get('content', ''))[:50]}...")
    
    session1.close()
    
    print("\n\n=== ステップ2: 新しいセッションを作成して手動で履歴を追加 ===")
    
    # 新しいセッションを作成
    session2 = SQLiteSession(session_id + "-2")
    
    # 手動で履歴を追加
    await session2.add_items(items1)
    
    # 履歴が正しく追加されたか確認
    print("\n=== セッション2の内容（復元後） ===")
    items2 = await session2.get_items()
    print(f"アイテム数: {len(items2)}")
    
    # 続きの質問
    result2 = await Runner.run(agent, "4番目の果物について詳しく教えてください", session=session2)
    print(f"\nUser: 4番目の果物について詳しく教えてください")
    print(f"Assistant: {result2.final_output[:200]}...")
    
    session2.close()
    
    print("\n\n=== ステップ3: 実際のLangfuseデータ形式を確認 ===")
    
    # 実際のセッションIDを入力
    real_session_id = input("\nテストするLangfuseセッションIDを入力（Enterでスキップ）: ").strip()
    
    if real_session_id:
        loader = ConversationHistoryLoader()
        traces = loader.get_session_traces(real_session_id)
        
        if traces and len(traces) > 0:
            print(f"\n最初のトレースの構造:")
            first_trace = traces[0]
            print(f"Keys: {list(first_trace.keys())}")
            
            if 'input' in first_trace:
                print(f"\nInput type: {type(first_trace['input'])}")
                print(f"Input: {str(first_trace['input'])[:200]}...")
            
            if 'output' in first_trace:
                print(f"\nOutput type: {type(first_trace['output'])}")
                print(f"Output: {str(first_trace['output'])[:200]}...")


if __name__ == "__main__":
    asyncio.run(test_session_recovery())