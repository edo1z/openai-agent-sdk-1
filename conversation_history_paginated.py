"""
ページネーション対応版の会話履歴取得
"""
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import httpx
import base64

load_dotenv()

class ConversationHistoryLoaderPaginated:
    def __init__(self):
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        # Basic認証ヘッダーを作成
        auth_string = f"{self.public_key}:{self.secret_key}"
        self.auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
    
    def get_all_session_observations(self, session_id: str, max_pages: int = 10) -> List[Dict]:
        """セッションIDで全observationsを取得（ページネーション対応）"""
        
        all_observations = []
        page = 1
        
        while page <= max_pages:
            # Langfuse APIエンドポイント
            url = f"{self.host}/api/public/observations"
            
            # クエリパラメータ
            params = {
                "sessionId": session_id,
                "limit": 100,  # API最大値
                "page": page
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
                observations = data.get("data", [])
                
                if not observations:
                    # これ以上データがない
                    break
                
                all_observations.extend(observations)
                
                # 次のページがあるかチェック
                meta = data.get("meta", {})
                if page >= meta.get("totalPages", 1):
                    break
                
                page += 1
            else:
                print(f"Error fetching observations page {page}: {response.status_code}")
                print(f"Response: {response.text}")
                break
        
        print(f"取得したobservations総数: {len(all_observations)} (ページ数: {page})")
        return all_observations
    
    def extract_conversation_history_paginated(self, session_id: str) -> List[Dict[str, str]]:
        """セッションIDから会話履歴を抽出（ページネーション対応）"""
        
        # セッションの全observationsを取得
        observations = self.get_all_session_observations(session_id)
        
        if not observations:
            return []
        
        # observationsを時系列順にソート
        sorted_obs = sorted(observations, key=lambda x: x.get("startTime", ""))
        
        conversation = []
        
        # user-interactionスパンごとに会話を抽出
        current_trace_id = None
        user_input = None
        
        for obs in sorted_obs:
            trace_id = obs.get("traceId")
            
            # 新しいトレース（会話のターン）の開始
            if trace_id != current_trace_id:
                current_trace_id = trace_id
                user_input = None
            
            # ユーザー入力を取得
            if obs.get("type") == "SPAN" and obs.get("name") == "user-interaction" and obs.get("input"):
                user_input = obs["input"]
                conversation.append({
                    "role": "user",
                    "content": str(user_input)
                })
            
            # アシスタントの最終応答を取得
            elif obs.get("type") == "GENERATION" and obs.get("output"):
                # 同じトレース内の最後のGENERATIONを使用
                output = obs["output"]
                # 既に同じトレースのアシスタント応答がある場合は更新
                if conversation and conversation[-1].get("role") == "assistant" and conversation[-1].get("trace_id") == trace_id:
                    conversation[-1]["content"] = str(output)
                else:
                    conversation.append({
                        "role": "assistant",
                        "content": str(output),
                        "trace_id": trace_id  # デバッグ用
                    })
        
        # trace_idを除去
        for msg in conversation:
            msg.pop("trace_id", None)
        
        return conversation


# 使用例
if __name__ == "__main__":
    session_id = input("セッションIDを入力: ").strip()
    if session_id:
        loader = ConversationHistoryLoaderPaginated()
        conversation = loader.extract_conversation_history_paginated(session_id)
        
        print(f"\n取得したメッセージ数: {len(conversation)}")
        
        # 最初と最後のメッセージを表示
        if conversation:
            print(f"\n最初のメッセージ:")
            print(f"  {conversation[0]['role']}: {conversation[0]['content'][:100]}...")
            
            if len(conversation) > 1:
                print(f"\n最後のメッセージ:")
                print(f"  {conversation[-1]['role']}: {conversation[-1]['content'][:100]}...")