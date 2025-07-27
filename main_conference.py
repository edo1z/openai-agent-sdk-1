"""
会議形式の専門家エージェントシステム
司会者と専門家の発言を明確に分離して表示
"""
import asyncio
import yaml
import uuid
import os
import base64
from typing import List, Dict, Any, Optional
from agents import Agent, Runner
from redis_session import RedisSession, create_redis_session
from facilitator_agent import FacilitatorAgent
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
    service_name='conference-agent-system',
    send_to_logfire=False
)
logfire.instrument_openai_agents()


def load_experts_config(file_path: str = "experts.yaml") -> Dict[str, Any]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_expert_agents(config: Dict[str, Any]) -> List[Agent]:
    """専門家エージェントを作成"""
    expert_agents = []
    for expert in config.get('experts', []):
        # 専門家としての発言を促すインストラクション
        enhanced_instructions = f"""あなたは{expert['name']}として発言してください。

{expert['instructions']}

重要：
- 必ず「{expert['name']}です。」という自己紹介から始めてください
- 専門家としての立場から発言してください
- 質問に対して的確で詳細な回答を提供してください
"""
        
        agent = Agent(
            name=expert['name'],
            handoff_description=expert['description'],
            instructions=enhanced_instructions
        )
        expert_agents.append(agent)
    return expert_agents


async def save_message(session: RedisSession, role: str, content: str, speaker: Optional[str] = None):
    """発言をセッションに保存（Runner.runが自動保存しない場合のみ使用）"""
    # 注意: Runner.runを使用する場合、入力と出力は自動的に保存されるため、
    # この関数は主に会話履歴の表示形式を調整する場合に使用する
    
    # OpenAI APIの標準フォーマットに準拠
    message = {
        "role": role,
        "content": content
    }
    
    # 発言者情報はcontentに含める（会議形式を維持）
    if speaker and role == "assistant":
        message["content"] = f"【{speaker}】\n{content}"
    
    await session.add_items([message])


async def display_recent_conversation(session: RedisSession, display_count: int = 10):
    """最近の会話履歴を表示"""
    items = await session.get_items(limit=display_count)
    
    if not items:
        return
    
    print(f"\n=== 直近の会議記録 ===")
    
    for i, item in enumerate(items, start=1):
        role = item.get("role", "")
        content = item.get("content", "")
        
        # 発言者を識別
        if role == "user":
            print(f"\n[{i}] 【ユーザー】")
        elif role == "assistant" and content.startswith("【"):
            # 発言者情報が含まれている場合は抽出して表示
            lines = content.split('\n', 1)
            if len(lines) > 0:
                speaker_line = lines[0]  # 【発言者】の部分
                actual_content = lines[1] if len(lines) > 1 else ""
                print(f"\n[{i}] {speaker_line}")
                content = actual_content
        else:
            print(f"\n[{i}] 【発言者】")
        
        if len(content) > 200:
            content = content[:200] + "..."
        
        print(f"    {content}")
    
    print("\n" + "="*50)
    print("会議を再開します...")
    print("="*50)


async def main():
    print("会議形式専門家システムを起動中...")
    print("司会者と専門家が順番に発言します")
    
    # 既存のセッションIDがあるか確認
    resume_session_id = input("\n既存の会議を再開しますか？ セッションIDを入力（新規の場合はEnter）: ").strip()
    
    if resume_session_id:
        session_id = resume_session_id
        print(f"\n会議セッション {session_id} を再開します...")
        
        # RedisSessionを作成（既存データを復元）
        session = await create_redis_session(session_id, restore_existing=True)
        
        # セッション情報を確認
        session_info = await session.get_session_info()
        
        if session_info["exists"]:
            print(f"\n過去の会議記録（{session_info['item_count']}発言）を読み込みました")
            
            # 最近の会話履歴を表示
            await display_recent_conversation(session)
            
            # TTLを延長
            await session.extend_ttl()
        else:
            print("過去の会議記録が見つかりませんでした。新規会議として開始します。")
    else:
        # 新規セッション
        session_id = str(uuid.uuid4())
        print(f"\n新規会議セッション {session_id} を開始します...")
        
        # 新しいRedisSessionを作成
        session = await create_redis_session(session_id, restore_existing=False)
    
    # 設定ファイルを読み込み
    config = load_experts_config()
    
    # 専門家エージェントを作成
    expert_agents = create_expert_agents(config)
    expert_dict = {agent.name: agent for agent in expert_agents}
    
    print(f"\n参加者：")
    print(f"- 司会者")
    for agent in expert_agents:
        print(f"- {agent.name}")
    
    # 司会者エージェントを作成
    facilitator = FacilitatorAgent(expert_agents)
    
    print("\n会議を開始します。質問や議題を入力してください（'exit'で終了）:\n")
    
    try:
        while True:
            user_input = input("\n【ユーザー】: ").strip()
            
            if user_input.lower() == 'exit':
                print(f"\n会議を終了します。")
                print(f"セッションID: {session_id}")
                print("このIDを使用して、後で会議を再開できます。")
                
                # セッション情報を表示
                session_info = await session.get_session_info()
                print(f"記録された発言数: {session_info['item_count']}")
                if session_info['ttl_seconds']:
                    days = session_info['ttl_seconds'] // 86400
                    print(f"記録の有効期限: 約{days}日後")
                break
            
            if not user_input:
                continue
            
            try:
                # ユーザーの発言は Runner.run が自動的に保存するため、ここでは保存しない
                # await save_message(session, "user", user_input, "ユーザー")
                
                print("\n" + "-"*50)
                
                # 司会者が応答（会話履歴を含めて実行）
                with logfire.span("facilitator-response") as span:
                    span.set_attribute("langfuse.session.id", session_id)
                    
                    result = await Runner.run(
                        facilitator,
                        user_input,
                        session=session  # type: ignore  # 会話履歴を含める
                    )
                
                facilitator_response = result.final_output
                
                # 専門家への依頼をチェック（表示前に解析）
                expert_request = facilitator.parse_expert_request(facilitator_response)
                
                # 司会者の発言を表示・保存
                print("\n【司会者】:")
                if expert_request:
                    # 専門家への依頼がある場合は、JSON部分を自然な日本語に変換
                    expert_name = expert_request.get("expert")
                    question = expert_request.get("question")
                    
                    # JSON部分より前のテキストを取得
                    json_start = facilitator_response.find("【専門家指名】")
                    if json_start > 0:
                        pre_text = facilitator_response[:json_start].strip()
                        if pre_text:
                            print(pre_text)
                    
                    # 自然な日本語で専門家への依頼を表示
                    print(f"\nでは、{expert_name}さん、{question}")
                else:
                    # 専門家への依頼がない場合はそのまま表示
                    print(facilitator_response)
                
                # 司会者の応答は Runner.run が自動的に保存するため、ここでは保存しない
                # await save_message(session, "assistant", facilitator_response, "司会者")
                
                if expert_request:
                    expert_name = expert_request.get("expert")
                    question = expert_request.get("question")
                    
                    if expert_name in expert_dict:
                        print(f"\n（{expert_name}に発言を依頼中...）\n")
                        
                        # 専門家が応答
                        with logfire.span("expert-response") as span:
                            span.set_attribute("langfuse.session.id", session_id)
                            span.set_attribute("expert.name", expert_name)
                            
                            # 質問がある場合のみ実行
                            if question:
                                expert_result = await Runner.run(
                                    expert_dict[expert_name],
                                    question,
                                    session=session  # type: ignore  # 会話履歴を含める
                                )
                                
                                expert_response = expert_result.final_output
                        
                                # 専門家の発言を表示
                                print(f"【{expert_name}】:")
                                print(expert_response)
                                # 専門家の応答も Runner.run が自動的に保存するため、ここでは保存しない
                                # await save_message(session, "assistant", expert_response, expert_name)
                
                # TTLを延長
                await session.extend_ttl()
                    
            except Exception as e:
                print(f"\nエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()
                continue
                
    finally:
        # セッションを閉じる
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
