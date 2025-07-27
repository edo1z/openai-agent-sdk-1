"""
Langfuseから会話履歴を取得して、会話を継続するサンプル
"""
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import httpx
import base64

load_dotenv()

class ConversationHistoryLoader:
    def __init__(self):
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        # Basic認証ヘッダーを作成
        auth_string = f"{self.public_key}:{self.secret_key}"
        self.auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
    
    def get_session_traces(self, session_id: str) -> List[Dict]:
        """特定のsession_idのトレースを取得"""
        
        # Langfuse APIエンドポイント
        url = f"{self.host}/api/public/traces"
        
        # クエリパラメータ
        params = {
            "sessionId": session_id,
            "limit": 100
        }
        
        # HTTPリクエスト
        response = httpx.get(
            url,
            params=params,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"Error fetching traces: {response.status_code}")
            return []
    
    def get_trace_details(self, trace_id: str) -> Dict:
        """特定のトレースの詳細を取得"""
        
        # Langfuse APIエンドポイント
        url = f"{self.host}/api/public/traces/{trace_id}"
        
        # HTTPリクエスト
        response = httpx.get(
            url,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching trace details: {response.status_code}")
            return {}
    
    def get_observations(self, trace_id: str) -> List[Dict]:
        """トレースのobservationsを取得"""
        
        # Langfuse APIエンドポイント
        url = f"{self.host}/api/public/observations"
        
        # クエリパラメータ
        params = {
            "traceId": trace_id,
            "limit": 100
        }
        
        # HTTPリクエスト
        response = httpx.get(
            url,
            params=params,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"Error fetching observations: {response.status_code}")
            return []
    
    def extract_conversation_history(self, traces: List[Dict]) -> List[Dict[str, str]]:
        """トレースから会話履歴を抽出"""
        conversation = []
        
        for trace in traces:
            trace_id = trace.get("id")
            if not trace_id:
                continue
                
            # 各トレースのobservationsを取得
            observations = self.get_observations(trace_id)
            
            # observationsを時系列順にソート
            sorted_obs = sorted(observations, key=lambda x: x.get("startTime", ""))
            
            # 各トレースでのユーザー入力とアシスタント応答を抽出
            user_input = None
            assistant_output = None
            
            for obs in sorted_obs:
                # ユーザー入力を探す
                if obs.get("input") and not user_input:
                    user_input = obs["input"]
                
                # アシスタントの最終応答を探す（最後のGENERATIONを使用）
                if obs.get("type") == "GENERATION" and obs.get("output"):
                    assistant_output = obs["output"]
            
            # ペアを追加
            if user_input:
                conversation.append({
                    "role": "user",
                    "content": str(user_input)
                })
            
            if assistant_output:
                conversation.append({
                    "role": "assistant",
                    "content": str(assistant_output)
                })
        
        return conversation
    
    def format_for_agent(self, conversation: List[Dict[str, str]]) -> str:
        """エージェントに渡すための会話履歴をフォーマット"""
        formatted = "過去の会話履歴:\n\n"
        
        for msg in conversation:
            role = "ユーザー" if msg["role"] == "user" else "アシスタント"
            formatted += f"{role}: {msg['content']}\n\n"
        
        return formatted


# 使用例
async def resume_conversation(session_id: str):
    """既存のセッションから会話を再開"""
    from agents import Agent, Runner, SQLiteSession
    
    # 履歴を取得
    loader = ConversationHistoryLoader()
    traces = loader.get_session_traces(session_id)
    conversation = loader.extract_conversation_history(traces)
    
    if conversation:
        print("過去の会話を読み込みました：")
        for msg in conversation[-4:]:  # 直近2往復を表示
            print(f"{msg['role']}: {msg['content'][:50]}...")
    
    # 既存のセッションを使用（または新規作成）
    session = SQLiteSession(session_id)
    
    # 会話履歴をコンテキストとして含めることも可能
    context_prompt = loader.format_for_agent(conversation)
    
    # エージェントの設定（main.pyから）
    # ... エージェント設定コード ...
    
    print("\n会話を続けてください:")
    # ... 会話ループ ...


if __name__ == "__main__":
    # テスト用: 特定のセッションIDの履歴を取得
    loader = ConversationHistoryLoader()
    
    # 例: 既存のセッションIDを指定
    session_id = "your-session-id-here"
    traces = loader.get_session_traces(session_id)
    
    if traces:
        print(f"Found {len(traces)} traces for session {session_id}")
        conversation = loader.extract_conversation_history(traces)
        print(f"Extracted {len(conversation)} messages")
    else:
        print("No traces found")