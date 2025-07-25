import asyncio
import yaml
import uuid
from typing import List, Dict, Any
from agents import Agent, Runner, SQLiteSession
from dotenv import load_dotenv
from log import langfuse_logger

load_dotenv()

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
    
    # ターン数をカウント
    turn_count = 0
    first_input = True
    
    while True:
        # ユーザー入力を取得
        user_input = input("\nあなた: ").strip()
        
        if user_input.lower() == 'exit':
            print("\nシステムを終了します。ありがとうございました。")
            break
        
        if not user_input:
            continue
        
        # 最初の入力時にLangfuseセッションを開始
        if first_input:
            langfuse_logger.start_session(session_id, initial_input=user_input)
            first_input = False
        
        try:
            # エージェントを実行
            print("\n専門家が回答を準備中...\n")
            result = await Runner.run(
                triage_agent,
                user_input,
                session=session
            )
            
            # 会話ターンを記録（ユーザー入力とエージェント応答をペアで）
            # TODO: 実際の会話履歴やプロンプトを取得する方法を検討
            langfuse_logger.log_turn(
                user_input=user_input,
                agent_response=result.final_output,
                agent_name="Expert Agent"
            )
            
            turn_count += 1
            
            # 応答を表示
            print(f"\n専門家の回答:\n{result.final_output}")
            
            # セッション情報を表示（デバッグ用）
            print(f"\n[セッションID: {session_id}]")
            
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            continue
    
    # ループ終了時にLangfuseセッションを終了
    langfuse_logger.end_session(total_turns=turn_count)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # Langfuseのバッファをフラッシュ
        langfuse_logger.flush()
