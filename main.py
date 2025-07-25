import asyncio
import yaml
import uuid
import os
import base64
from typing import List, Dict, Any
from agents import Agent, Runner, SQLiteSession
from dotenv import load_dotenv
import logfire

# 環境変数を読み込む
load_dotenv()

# OpenTelemetryエンドポイントをLangfuseに設定
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    # Build Basic Auth header
    LANGFUSE_AUTH = base64.b64encode(
        f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
    ).decode()
    
    # Configure OpenTelemetry endpoint & headers
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com") + "/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

# Langfuse統合をセットアップ
logfire.configure(
    service_name='expert-agent-system',
    send_to_logfire=False  # Logfireには送信せず、Langfuseのみに送信
)
logfire.instrument_openai_agents()

def load_experts_config(file_path: str = "experts.yaml") -> Dict[str, Any]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_expert_agents(config: Dict[str, Any]) -> List[Agent]:
    expert_agents = []
    for expert in config.get('experts', []):
        agent = Agent(
            name=expert['name'],
            handoff_description=expert['description'],
            instructions=expert['instructions']
        )
        expert_agents.append(agent)
    return expert_agents

def create_triage_agent(expert_agents: List[Agent]) -> Agent:
    expert_list = "\n".join([f"- {agent.name}: {agent.handoff_description}" for agent in expert_agents])
    
    return Agent(
        name="Triage Agent",
        instructions=f"""あなたはユーザーの質問を分析して、最適な専門家を選択するトリアージエージェントです。

利用可能な専門家:
{expert_list}

ユーザーの質問内容を理解し、最も適切な専門家にハンドオフしてください。
質問が複数の分野にまたがる場合は、主要な部分に最も適した専門家を選んでください。
""",
        handoffs=list(expert_agents)  # 明示的にlistに変換
    )


async def main():
    print("専門家エージェントシステムを起動中...")
    
    # 設定ファイルを読み込み
    config = load_experts_config()
    
    # 専門家エージェントを作成
    expert_agents = create_expert_agents(config)
    print(f"{len(expert_agents)}人の専門家を読み込みました")
    
    # トリアージエージェントを作成
    triage_agent = create_triage_agent(expert_agents)
    
    print("\n専門家エージェントシステムが開始されました。")
    print("質問を入力してください（'exit'で終了）:\n")
    
    # セッションIDを生成（会話全体で1つ）
    session_id = str(uuid.uuid4())
    
    # SQLiteSessionを作成（インメモリ）
    session = SQLiteSession(session_id)
    
    while True:
        # ユーザー入力を取得
        user_input = input("\nあなた: ").strip()
        
        if user_input.lower() == 'exit':
            print("\nシステムを終了します。ありがとうございました。")
            break
        
        if not user_input:
            continue
        
        try:
            # エージェントを実行（自動的にトレースされる）
            print("\n専門家が回答を準備中...\n")
            result = await Runner.run(
                triage_agent,
                user_input,
                session=session
            )
            
            # 応答を表示
            print(f"\n専門家の回答:\n{result.final_output}")
            
            # セッション情報を表示（デバッグ用）
            print(f"\n[セッションID: {session_id}]")
                
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())