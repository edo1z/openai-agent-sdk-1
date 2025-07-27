"""
Session protocolの互換性をテスト
"""
import asyncio
from typing import Protocol, List, Dict, Any, runtime_checkable
from redis_session import RedisSession, create_redis_session
from agents import Session, Agent, Runner
import uuid


@runtime_checkable
class SessionProtocol(Protocol):
    """OpenAI Agents SDKが期待するSession protocol"""
    async def get_items(self, limit: int | None = None) -> list:
        ...
    
    async def add_items(self, items: list) -> None:
        ...
    
    async def pop_item(self) -> dict | None:
        ...
    
    async def clear_session(self) -> None:
        ...


async def test_protocol_compliance():
    """RedisSessionがSession protocolに準拠しているかテスト"""
    
    print("=== Session Protocol互換性テスト ===\n")
    
    # RedisSessionのインスタンスを作成
    session_id = f"test-protocol-{uuid.uuid4()}"
    redis_session = await create_redis_session(session_id)
    
    # 1. Protocolチェック
    print(f"1. RedisSessionはSessionProtocolに準拠？: {isinstance(redis_session, SessionProtocol)}")
    
    # 2. メソッドの存在確認
    print("\n2. 必要なメソッドの存在確認:")
    required_methods = ['get_items', 'add_items', 'pop_item', 'clear_session']
    for method in required_methods:
        has_method = hasattr(redis_session, method)
        print(f"   - {method}: {'✓' if has_method else '✗'}")
    
    # 3. 実際の使用テスト
    print("\n3. 実際の使用テスト:")
    
    # テストエージェントを作成
    test_agent = Agent(
        name="Test Agent",
        instructions="You are a test agent. Just respond with 'Test response'."
    )
    
    try:
        # Runner.runで使用
        result = await Runner.run(
            test_agent,
            "Test message",
            session=redis_session
        )
        print(f"   Runner.run成功: {result.final_output[:50]}...")
        
        # セッションの内容を確認
        items = await redis_session.get_items()
        print(f"   セッション内のアイテム数: {len(items)}")
        
    except Exception as e:
        print(f"   エラー: {type(e).__name__}: {e}")
    
    finally:
        await redis_session.clear_session()
        await redis_session.close()
    
    # 4. 型アノテーションの確認
    print("\n4. 型アノテーションの確認:")
    import inspect
    
    # get_itemsのシグネチャ
    get_items_sig = inspect.signature(redis_session.get_items)
    print(f"   get_items: {get_items_sig}")
    
    # add_itemsのシグネチャ
    add_items_sig = inspect.signature(redis_session.add_items)
    print(f"   add_items: {add_items_sig}")


async def test_with_typing():
    """型チェックでの互換性テスト"""
    print("\n\n=== 型チェック互換性テスト ===\n")
    
    session_id = f"test-typing-{uuid.uuid4()}"
    redis_session = await create_redis_session(session_id)
    
    # Session型として使用できるか？
    def use_session(session: Session) -> None:
        print(f"Session型として受け取れました: {type(session)}")
    
    try:
        # これは実行時には動作するが、型チェッカーでエラーになる
        use_session(redis_session)  # type: ignore
    except Exception as e:
        print(f"エラー: {e}")
    
    await redis_session.close()


if __name__ == "__main__":
    asyncio.run(test_protocol_compliance())
    asyncio.run(test_with_typing())