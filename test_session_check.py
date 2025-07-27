"""
セッションがLangfuseに正しく記録されているか確認
"""
from conversation_history import ConversationHistoryLoader
import time

def check_session_data(session_id: str):
    """セッションデータを詳しく確認"""
    
    loader = ConversationHistoryLoader()
    
    print(f"\n=== セッション {session_id} の確認 ===")
    
    # 1. Traces APIで確認
    traces = loader.get_session_traces(session_id)
    print(f"\nTraces数: {len(traces)}")
    
    if traces:
        print("\nTraces詳細:")
        for i, trace in enumerate(traces[:3]):  # 最初の3つ
            print(f"\n{i+1}. Trace ID: {trace.get('id')}")
            print(f"   Name: {trace.get('name')}")
            print(f"   Timestamp: {trace.get('timestamp')}")
            print(f"   SessionId: {trace.get('sessionId')}")
    
    # 2. Observations APIで確認
    observations = loader.get_session_observations(session_id)
    print(f"\nObservations数: {len(observations)}")
    
    if observations:
        print("\nObservations詳細:")
        for i, obs in enumerate(observations[:5]):  # 最初の5つ
            print(f"\n{i+1}. Type: {obs.get('type')}")
            print(f"   Name: {obs.get('name')}")
            print(f"   TraceId: {obs.get('traceId')}")
            print(f"   Input: {str(obs.get('input'))[:50] if obs.get('input') else 'None'}")
            print(f"   Output: {str(obs.get('output'))[:50] if obs.get('output') else 'None'}")
    
    # 3. 会話履歴の抽出を試す
    conversation = loader.extract_conversation_history_direct(session_id)
    print(f"\n抽出された会話数: {len(conversation)}")
    
    if conversation:
        print("\n会話履歴:")
        for i, msg in enumerate(conversation):
            print(f"{i+1}. [{msg['role']}] {msg['content'][:50]}...")


if __name__ == "__main__":
    # 直近のセッションをチェック
    session_id = "d73a44e0-c425-4eac-b853-55a2ff1b1444"
    
    print("即座にチェック...")
    check_session_data(session_id)
    
    print("\n\n5秒待機後に再チェック（Langfuseへの反映遅延の可能性）...")
    time.sleep(5)
    check_session_data(session_id)