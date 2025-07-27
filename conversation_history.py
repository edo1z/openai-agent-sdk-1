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
    
    def get_session_observations(self, session_id: str) -> List[Dict]:
        """セッションIDで全observationsを一括取得"""
        
        # Langfuse APIエンドポイント
        url = f"{self.host}/api/public/observations"
        
        # クエリパラメータ
        params = {
            "sessionId": session_id,
            "limit": 100  # API最大値
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
            print(f"Response: {response.text}")
            return []
    
    def extract_conversation_history_direct(self, session_id: str) -> List[Dict[str, str]]:
        """セッションIDから会話履歴を抽出（Traces経由で正しくフィルタリング）"""
        
        # Langfuseの制限により、observations APIは直接sessionIdでフィルタできない
        # 代わりにtraces経由でobservationsを取得する（公式推奨の方法）
        
        # 1. まずセッションのトレースを取得
        traces = self.get_session_traces(session_id)
        if not traces:
            return []
        
        all_observations = []
        
        # 2. 各トレースのobservationsを取得
        for trace in traces:
            trace_id = trace.get("id")
            observations = self.get_observations(trace_id)
            all_observations.extend(observations)
        
        # 3. observationsを時系列順にソート
        sorted_obs = sorted(all_observations, key=lambda x: x.get("startTime", ""))
        
        conversation = []
        processed_messages = set()  # 重複防止用
        
        # 4. GENERATIONタイプから会話を抽出
        for obs in sorted_obs:
            if obs.get("type") == "GENERATION" and obs.get("input"):
                messages = obs.get("input", [])
                
                # 各メッセージを処理
                for msg in messages:
                    if isinstance(msg, dict) and "content" in msg and "role" in msg:
                        role = msg.get("role")
                        content = msg.get("content")
                        
                        # システムメッセージはスキップ
                        if role == "system":
                            continue
                        
                        # メッセージのハッシュを作成（重複チェック用）
                        msg_hash = f"{role}:{content}"
                        
                        # 新しいメッセージのみ追加
                        if msg_hash not in processed_messages:
                            processed_messages.add(msg_hash)
                            conversation.append({
                                "role": "user" if role == "user" else "assistant",
                                "content": content
                            })
        
        # 5. 最新のGENERATIONのメッセージのみを保持（重複を除去）
        # 各GENERATIONには累積的な会話履歴が含まれるため、最新のものが最も完全
        if conversation:
            # 最後のGENERATIONから抽出された会話履歴を返す
            # これにより、古い重複データは自動的に除外される
            final_conversation = []
            seen_content = set()
            
            # 後ろから処理して、最新の状態を優先
            for msg in reversed(conversation):
                content_key = f"{msg['role']}:{msg['content']}"
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    final_conversation.insert(0, msg)
            
            # 指定されたセッションの会話のみを返す
            # （最後のN個のメッセージが現在のセッションのもの）
            trace_count = len(traces)
            # 各トレースは通常2つのメッセージ（user + assistant）を含む
            expected_messages = trace_count * 2
            
            # 最後のexpected_messages個を返す
            return final_conversation[-expected_messages:] if len(final_conversation) > expected_messages else final_conversation
        
        return conversation
    
    def extract_conversation_history(self, traces: List[Dict]) -> List[Dict[str, str]]:
        """トレースから会話履歴を抽出（後方互換性）"""
        if not traces:
            return []
        
        session_id = traces[0].get("sessionId")
        if not session_id:
            return []
        
        return self.extract_conversation_history_direct(session_id)
    
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