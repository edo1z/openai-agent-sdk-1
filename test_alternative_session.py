"""
セッションIDを設定する代替方法をテスト
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
    service_name='alternative-session-test',
    send_to_logfire=False
)
logfire.instrument_openai_agents()


async def test_alternative_session():
    """代替セッション設定方法をテスト"""
    
    # テスト用のID
    test_id = str(uuid.uuid4())
    print(f"テストID: {test_id}")
    
    # エージェントを作成
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful test agent."
    )
    
    # SQLiteSessionを作成（引数名を変えてみる）
    conversation_id = test_id  # sessionという名前を避ける
    session = SQLiteSession(conversation_id)
    
    print("\n=== 方法1: トレースレベルで設定 ===")
    with logfire.trace(name=f"conversation-{test_id}") as trace:
        trace.set_attribute("langfuse.conversationId", test_id)
        trace.set_attribute("langfuse.metadata.conversationId", test_id)
        
        result = await Runner.run(agent, "Test message 1", session=session)
        print(f"Response: {result.final_output[:50]}...")
    
    print("\n=== 方法2: 環境変数で設定 ===")
    # 一時的に環境変数を設定
    os.environ["LANGFUSE_SESSION_ID"] = test_id
    os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"langfuse.conversation.id={test_id}"
    
    result = await Runner.run(agent, "Test message 2", session=session)
    print(f"Response: {result.final_output[:50]}...")
    
    # 環境変数をクリア
    os.environ.pop("LANGFUSE_SESSION_ID", None)
    os.environ.pop("OTEL_RESOURCE_ATTRIBUTES", None)
    
    print("\n=== 方法3: Baggage（コンテキスト伝播）を使用 ===")
    from opentelemetry import baggage
    from opentelemetry.context import attach, detach
    
    # Baggageを設定
    token = attach(baggage.set_baggage("conversation.id", test_id))
    try:
        with logfire.span("with-baggage") as span:
            # Baggageから値を取得して属性に設定
            conv_id = baggage.get_baggage("conversation.id")
            if conv_id:
                span.set_attribute("langfuse.conversationId", conv_id)
            
            result = await Runner.run(agent, "Test message 3", session=session)
            print(f"Response: {result.final_output[:50]}...")
    finally:
        detach(token)
    
    print(f"\n全テスト完了。")
    print(f"Langfuseで '{test_id}' が表示されるか確認してください。")
    
    session.close()


if __name__ == "__main__":
    asyncio.run(test_alternative_session())