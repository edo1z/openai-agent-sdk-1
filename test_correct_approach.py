"""
正しいアプローチ：TracesからObservationsを取得
"""
from conversation_history import ConversationHistoryLoader
import httpx
import base64
import os
from dotenv import load_dotenv

load_dotenv()

def get_observations_by_traces(session_id: str):
    """トレース経由で正しくobservationsを取得"""
    
    loader = ConversationHistoryLoader()
    
    # 1. まずトレースを取得（これは正しくフィルタされている）
    traces = loader.get_session_traces(session_id)
    print(f"セッション {session_id} のトレース数: {len(traces)}")
    
    all_observations = []
    
    # 2. 各トレースのobservationsを個別に取得
    for trace in traces:
        trace_id = trace.get("id")
        observations = loader.get_observations(trace_id)
        
        print(f"\nTrace {trace_id[:8]}... のobservations数: {len(observations)}")
        
        # GENERATIONタイプを探す
        for obs in observations:
            if obs.get("type") == "GENERATION" and obs.get("input"):
                all_observations.append(obs)
    
    print(f"\n合計GENERATION数: {len(all_observations)}")
    
    # 3. 会話を抽出
    conversation = []
    for obs in all_observations:
        input_data = obs.get("input", [])
        if isinstance(input_data, list):
            for msg in input_data:
                if isinstance(msg, dict) and "content" in msg and "role" in msg:
                    role = msg.get("role")
                    if role != "system":
                        conversation.append({
                            "role": "user" if role == "user" else "assistant",
                            "content": msg.get("content")
                        })
    
    # 重複を削除（最新のものを保持）
    unique_conversation = []
    seen = set()
    
    for msg in reversed(conversation):
        key = f"{msg['role']}:{msg['content']}"
        if key not in seen:
            seen.add(key)
            unique_conversation.insert(0, msg)
    
    print(f"\n抽出された会話数: {len(unique_conversation)}")
    
    # 最後の6メッセージを表示
    print("\n=== 会話履歴（最後の6メッセージ）===")
    for i, msg in enumerate(unique_conversation[-6:]):
        role = "USER" if msg["role"] == "user" else "ASST"
        content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        print(f"{i+1}. [{role}] {content}")
    
    return unique_conversation


if __name__ == "__main__":
    session_id = "d73a44e0-c425-4eac-b853-55a2ff1b1444"
    get_observations_by_traces(session_id)