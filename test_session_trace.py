"""
session_idがLangfuseに正しく送信されるかテストするスクリプト
"""
import asyncio
import os
import base64
import uuid
from agents import Agent, Runner, SQLiteSession
from dotenv import load_dotenv
import logfire

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
    service_name='test-session-trace',
    send_to_logfire=False
)
logfire.instrument_openai_agents()


async def test_session_trace():
    """session_idのトレースをテスト"""
    
    # テスト用のセッションID
    session_id = f"test-{uuid.uuid4()}"
    print(f"テストセッションID: {session_id}")
    
    # シンプルなエージェントを作成
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful test agent."
    )
    
    # SQLiteSessionを作成
    session = SQLiteSession(session_id)
    
    # 異なる方法でsession_idを設定してテスト
    
    print("\n=== 方法1: 正しいLangfuse属性名 ===")
    with logfire.span("test-with-langfuse-session") as span:
        span.set_attribute("langfuse.session.id", session_id)
        result = await Runner.run(agent, "Test message 1", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print("\n=== 方法2: ルートスパンに設定 ===")
    with logfire.span("root-span") as root_span:
        root_span.set_attribute("langfuse.session.id", session_id)
        root_span.set_attribute("langfuse.trace.name", f"Session Test {session_id}")
        result = await Runner.run(agent, "Test message 2", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print("\n=== 方法3: 複数の属性を設定 ===")
    with logfire.span("full-attributes") as span:
        span.set_attribute("langfuse.session.id", session_id)
        span.set_attribute("langfuse.user.id", "test-user")
        span.set_attribute("langfuse.trace.name", "Test Trace")
        result = await Runner.run(agent, "Test message 3", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print(f"\n全テスト完了。Langfuseでセッション '{session_id}' を確認してください。")
    session.close()


if __name__ == "__main__":
    asyncio.run(test_session_trace())