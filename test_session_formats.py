"""
様々な形式でsession IDを送信してテスト
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
    service_name='session-format-test',
    send_to_logfire=False
)
logfire.instrument_openai_agents()


async def test_session_formats():
    """様々な形式でsession IDをテスト"""
    
    # テスト用のセッションID
    session_id = f"format-test-{uuid.uuid4()}"
    print(f"テストセッションID: {session_id}")
    
    # シンプルなエージェントを作成
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful test agent."
    )
    
    # SQLiteSessionを作成
    session = SQLiteSession(session_id)
    
    print("\n=== 形式1: langfuse.session.id ===")
    with logfire.span("format-1-dot-notation") as span:
        span.set_attribute("langfuse.session.id", session_id)
        result = await Runner.run(agent, "Test format 1", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print("\n=== 形式2: langfuse.sessionId ===")
    with logfire.span("format-2-camelCase") as span:
        span.set_attribute("langfuse.sessionId", session_id)
        result = await Runner.run(agent, "Test format 2", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print("\n=== 形式3: sessionId (without prefix) ===")
    with logfire.span("format-3-no-prefix") as span:
        span.set_attribute("sessionId", session_id)
        result = await Runner.run(agent, "Test format 3", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print("\n=== 形式4: session_id (snake_case) ===")
    with logfire.span("format-4-snake-case") as span:
        span.set_attribute("session_id", session_id)
        result = await Runner.run(agent, "Test format 4", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print("\n=== 形式5: langfuse.metadata.sessionId ===")
    with logfire.span("format-5-metadata") as span:
        span.set_attribute("langfuse.metadata.sessionId", session_id)
        result = await Runner.run(agent, "Test format 5", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print(f"\n全テスト完了。")
    print(f"Langfuseで以下を確認してください：")
    print(f"1. セッション '{session_id}' が表示されるか")
    print(f"2. どの形式が正しく認識されるか")
    print(f"3. '[Scrubbed due to 'session']'が表示されるか")
    
    session.close()


if __name__ == "__main__":
    asyncio.run(test_session_formats())