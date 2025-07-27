"""
RedisSessionを使用した専門家エージェントシステム
"""
import asyncio
import yaml
import uuid
import os
import base64
from typing import List, Dict, Any, Optional
from agents import Agent, Runner
from redis_session import RedisSession, create_redis_session
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
    service_name='expert-agent-system',
    send_to_logfire=False
    # scrubbingパラメータを省略することでデフォルト（マスキング有効）になる
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


def create_triage_agent(expert_agents: List[Agent], context: Optional[str] = None) -> Agent:
    expert_list = "\n".join([f"- {agent.name}: {agent.handoff_description}" for agent in expert_agents])
    
    instructions = f"""あなたはユーザーの質問を分析して、最適な専門家を選択するトリアージエージェントです。

利用可能な専門家:
{expert_list}

ユーザーの質問内容を理解し、最も適切な専門家にハンドオフしてください。
質問が複数の分野にまたがる場合は、主要な部分に最も適した専門家を選んでください。
"""
    
    if context:
        instructions += f"\n\n{context}"
    
    return Agent(
        name="Triage Agent",
        instructions=instructions,
        handoffs=list(expert_agents)
    )


async def display_recent_conversation(session: RedisSession, display_count: int = 6):
    """最近の会話履歴を表示"""
    items = await session.get_items(limit=display_count)
    
    if not items:
        return
    
    print(f"\n=== 直近の会話履歴 ===")
    
    for i, item in enumerate(items, start=1):
        if item.get("role") == "user":
            # ユーザーメッセージ
            content = item.get("content", "")
            if len(content) > 150:
                content = content[:150] + "..."
            print(f"\n[{i}] あなた:")
            print(f"    {content}")
        elif item.get("role") == "assistant":
            # アシスタントメッセージ
            if isinstance(item.get("content"), list):
                # 複雑な形式のメッセージ
                for content_item in item["content"]:
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text", "")
                        if len(text) > 150:
                            text = text[:150] + "..."
                        print(f"\n[{i}] 専門家:")
                        print(f"    {text}")
                        break
            else:
                # シンプルな形式のメッセージ
                content = str(item.get("content", ""))
                if len(content) > 150:
                    content = content[:150] + "..."
                print(f"\n[{i}] 専門家:")
                print(f"    {content}")
    
    print("\n" + "="*50)
    print("会話を続けます...")
    print("="*50)


async def main():
    print("専門家エージェントシステムを起動中...")
    
    # 既存のセッションIDがあるか確認
    resume_session_id = input("既存のセッションを再開しますか？ セッションIDを入力（新規の場合はEnter）: ").strip()
    
    if resume_session_id:
        session_id = resume_session_id
        print(f"\nセッション {session_id} を再開します...")
        
        # RedisSessionを作成（既存データを復元）
        session = await create_redis_session(session_id, restore_existing=True)
        
        # セッション情報を確認
        session_info = await session.get_session_info()
        
        if session_info["exists"]:
            print(f"\n過去の会話（{session_info['item_count']}メッセージ）を読み込みました")
            
            # 最近の会話履歴を表示
            await display_recent_conversation(session)
            
            # TTLを延長
            await session.extend_ttl()
        else:
            print("過去の会話が見つかりませんでした。新規セッションとして開始します。")
    else:
        # 新規セッション
        session_id = str(uuid.uuid4())
        print(f"\n新規セッション {session_id} を開始します...")
        
        # 新しいRedisSessionを作成
        session = await create_redis_session(session_id, restore_existing=False)
    
    # 設定ファイルを読み込み
    config = load_experts_config()
    
    # 専門家エージェントを作成
    expert_agents = create_expert_agents(config)
    print(f"{len(expert_agents)}人の専門家を読み込みました")
    
    # トリアージエージェントを作成
    triage_agent = create_triage_agent(expert_agents)
    
    print("\n質問を入力してください（'exit'で終了）:\n")
    
    try:
        while True:
            user_input = input("\nあなた: ").strip()
            
            if user_input.lower() == 'exit':
                print(f"\nセッションを終了します。")
                print(f"セッションID: {session_id}")
                print("このIDを使用して、後で会話を再開できます。")
                
                # セッション情報を表示
                session_info = await session.get_session_info()
                print(f"保存されたメッセージ数: {session_info['item_count']}")
                if session_info['ttl_seconds']:
                    days = session_info['ttl_seconds'] // 86400
                    print(f"有効期限: 約{days}日後")
                break
            
            if not user_input:
                continue
            
            try:
                # エージェントを実行
                print("\n専門家が回答を準備中...\n")
                
                # Langfuseのsession_idを設定
                with logfire.span("user-interaction") as span:
                    span.set_attribute("langfuse.session.id", session_id)
                    result = await Runner.run(
                        triage_agent,
                        user_input,
                        session=session  # type: ignore
                    )
                
                # 応答を表示
                print(f"\n専門家の回答:\n{result.final_output}")
                
                # TTLを延長（アクティビティがあったため）
                await session.extend_ttl()
                    
            except Exception as e:
                print(f"\nエラーが発生しました: {e}")
                continue
                
    finally:
        # セッションを閉じる
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
