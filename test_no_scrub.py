"""
スクラビングを回避する方法をテスト
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

# スクラビングを無効化する可能性のある環境変数
os.environ["OTEL_REDACTION_ENABLED"] = "false"
os.environ["OTEL_SENSITIVE_DATA_REDACTION"] = "false"
os.environ["LANGFUSE_SCRUB_SENSITIVE"] = "false"

# OpenTelemetryエンドポイントをLangfuseに設定
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    LANGFUSE_AUTH = base64.b64encode(
        f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
    ).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com") + "/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

# Langfuse統合をセットアップ
logfire.configure(
    service_name='no-scrub-test',
    send_to_logfire=False,
    scrubbing=False  # スクラビングを無効化
)
logfire.instrument_openai_agents()


async def test_no_scrub():
    """スクラビングを回避してsession IDを送信"""
    
    # テスト用のセッションID
    test_id = f"noscrub-{uuid.uuid4()}"
    print(f"テストID: {test_id}")
    
    # シンプルなエージェントを作成
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful test agent."
    )
    
    # SQLiteSessionを作成
    session = SQLiteSession(test_id)
    
    print("\n=== 別の属性名を使用 ===")
    
    # "session"という文字列を避けて別の名前を使う
    alternatives = [
        ("langfuse.conversationId", "conversationId"),
        ("langfuse.threadId", "threadId"),
        ("langfuse.contextId", "contextId"),
        ("langfuse.traceGroup", "traceGroup"),
        ("langfuse.metadata.conversationId", "metadata.conversationId")
    ]
    
    for attr_name, display_name in alternatives:
        print(f"\n--- {display_name} として送信 ---")
        with logfire.span(f"test-{display_name}") as span:
            span.set_attribute(attr_name, test_id)
            result = await Runner.run(agent, f"Test with {display_name}", session=session)
            print(f"Response: {result.final_output[:50]}...")
    
    print(f"\n全テスト完了。")
    print(f"Langfuseで '{test_id}' が表示されるか確認してください。")
    
    session.close()


if __name__ == "__main__":
    asyncio.run(test_no_scrub())