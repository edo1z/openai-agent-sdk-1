"""
会話の再開機能を含むメインスクリプト
"""
import asyncio
import yaml
import uuid
import os
import base64
from typing import List, Dict, Any, Optional
from agents import Agent, Runner, SQLiteSession
from dotenv import load_dotenv
import logfire
from logfire import ScrubbingOptions, ScrubMatch
from conversation_history import ConversationHistoryLoader
from session_builder import SessionBuilder
from advanced_session_builder import AdvancedSessionBuilder

# 環境変数を読み込む
load_dotenv()

# OpenTelemetryエンドポイントをLangfuseに設定
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    LANGFUSE_AUTH = base64.b64encode(
        f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
    ).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com") + "/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

def scrubbing_callback(match: ScrubMatch):
    """Langfuseのsession IDをスクラビングから除外"""
    if (
        match.path == ("attributes", "langfuse.session.id")
        and match.pattern_match.group(0) == "session"
    ):
        # 元の値を返してスクラビングを防ぐ
        return match.value
    # Noneを返す（暗黙的）場合はスクラビングされる

# Langfuse統合をセットアップ
logfire.configure(
    service_name='expert-agent-system',
    send_to_logfire=False,
    scrubbing=ScrubbingOptions(callback=scrubbing_callback)  # カスタムスクラビング
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


async def main():
    print("専門家エージェントシステムを起動中...")
    
    # 既存のセッションIDがあるか確認
    resume_session_id = input("既存のセッションを再開しますか？ セッションIDを入力（新規の場合はEnter）: ").strip()
    
    if resume_session_id:
        session_id = resume_session_id
        print(f"\nセッション {session_id} を再開します...")
        
        # 会話履歴を取得
        loader = ConversationHistoryLoader()
        traces = loader.get_session_traces(session_id)
        
        if traces:
            conversation = loader.extract_conversation_history(traces)
            print(f"\n過去の会話（{len(conversation)}メッセージ）を読み込みました:")
            
            # 直近の会話を表示
            for msg in conversation[-4:]:  # 最後の2往復
                role = "あなた" if msg["role"] == "user" else "専門家"
                content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                print(f"{role}: {content}")
            
            print("\n--- 会話を続けます ---")
            
            # 既存の会話履歴をコンテキストに含める
            context = loader.format_for_agent(conversation[-10:])  # 直近10メッセージ
        else:
            print("過去の会話が見つかりませんでした。新規セッションとして開始します。")
    else:
        # 新規セッション
        session_id = str(uuid.uuid4())
        print(f"\n新規セッション {session_id} を開始します...")
    
    # 設定ファイルを読み込み
    config = load_experts_config()
    
    # 専門家エージェントを作成
    expert_agents = create_expert_agents(config)
    print(f"{len(expert_agents)}人の専門家を読み込みました")
    
    # トリアージエージェントを作成
    context = locals().get('context')  # 会話履歴のコンテキスト
    triage_agent = create_triage_agent(expert_agents, context)
    
    # インメモリSQLiteSessionを作成
    if resume_session_id:
        # Langfuseから詳細な履歴を復元（複数エージェント対応）
        session = await AdvancedSessionBuilder.rebuild_from_langfuse_advanced(session_id)
    else:
        # 新規セッション
        session = SQLiteSession(session_id)
    
    print("\n質問を入力してください（'exit'で終了）:\n")
    
    while True:
        user_input = input("\nあなた: ").strip()
        
        if user_input.lower() == 'exit':
            print(f"\nセッションを終了します。")
            print(f"セッションID: {session_id}")
            print("このIDを使用して、後で会話を再開できます。")
            session.close()  # DBコネクションを適切にクローズ
            break
        
        if not user_input:
            continue
        
        try:
            # エージェントを実行（自動的にトレースされる）
            print("\n専門家が回答を準備中...\n")
            
            # Langfuseのsession_idを正しい属性名で設定
            with logfire.span("user-interaction") as span:
                # langfuse.session.id（ドット区切り）が正しい形式
                span.set_attribute("langfuse.session.id", session_id)
                result = await Runner.run(
                    triage_agent,
                    user_input,
                    session=session
                )
            
            # 応答を表示
            print(f"\n専門家の回答:\n{result.final_output}")
                
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())