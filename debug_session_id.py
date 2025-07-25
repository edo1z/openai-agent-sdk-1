"""
session_idがどの段階でスクラブされるかデバッグ
"""
import asyncio
import uuid
from agents import Agent, Runner, SQLiteSession
import logfire
import os
import base64
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

# OpenTelemetryエンドポイントをLangfuseに設定
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    LANGFUSE_AUTH = base64.b64encode(
        f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
    ).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com") + "/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

# Langfuse統合をセットアップ
logfire.configure(
    service_name='debug-session-id',
    send_to_logfire=False
)
logfire.instrument_openai_agents()


async def debug_session_id():
    """session_idのデバッグ"""
    
    # 元のsession_id
    original_id = str(uuid.uuid4())
    print(f"1. 生成されたUUID: {original_id}")
    
    # SQLiteSessionを作成
    session = SQLiteSession(original_id)
    print(f"2. SQLiteSessionのsession_id: {session.session_id}")
    
    # エージェントを作成
    agent = Agent(
        name="Debug Agent",
        instructions="You are a helpful debug agent."
    )
    
    # 実行前にもう一度確認
    print(f"3. 実行直前のsession.session_id: {session.session_id}")
    
    # Runner.runを実行
    with logfire.span("debug-run") as span:
        # session_idを手動で属性に設定
        span.set_attribute("debug.original_id", original_id)
        span.set_attribute("debug.session_id", session.session_id)
        
        result = await Runner.run(agent, "Debug test", session=session)
        
        # 実行後のsession_idを確認
        print(f"4. 実行後のsession.session_id: {session.session_id}")
    
    # セッションの中身を確認
    items = await session.get_items()
    print(f"\n5. セッション内のアイテム数: {len(items)}")
    
    # SQLiteSessionの内部を確認（プライベート属性にアクセス）
    if hasattr(session, '_session_id'):
        print(f"6. session._session_id: {session._session_id}")
    
    print(f"\nLangfuseで以下を確認してください：")
    print(f"- debug.original_id: {original_id}")
    print(f"- debug.session_id: {session.session_id}")
    
    session.close()


if __name__ == "__main__":
    asyncio.run(debug_session_id())