"""
Langfuseから最近のセッションを一覧表示するスクリプト
"""
from conversation_history import ConversationHistoryLoader
import httpx
from datetime import datetime

def list_recent_sessions(limit=10):
    """最近のセッションを一覧表示"""
    
    loader = ConversationHistoryLoader()
    
    # Sessions APIエンドポイント（まずTracesから取得を試みる）
    url = f"{loader.host}/api/public/traces"
    
    response = httpx.get(
        url,
        headers={
            "Authorization": loader.auth_header,
            "Content-Type": "application/json"
        },
        params={
            "limit": 20  # 小さくしてタイムアウトを回避
        },
        timeout=30.0  # 30秒のタイムアウト
    )
    
    if response.status_code == 200:
        traces = response.json().get("data", [])
        
        # ユニークなセッションIDを収集
        sessions = {}
        for trace in traces:
            session_id = trace.get("sessionId")
            if session_id and session_id not in sessions:
                sessions[session_id] = {
                    "id": session_id,
                    "first_seen": trace.get("timestamp"),
                    "last_seen": trace.get("timestamp"),
                    "trace_count": 1,
                    "first_input": str(trace.get("input", ""))[:50]
                }
            elif session_id:
                sessions[session_id]["trace_count"] += 1
                sessions[session_id]["last_seen"] = trace.get("timestamp")
        
        # セッションを時系列で表示
        print(f"\n=== 最近のセッション（{len(sessions)}件）===\n")
        
        sorted_sessions = sorted(sessions.values(), 
                               key=lambda x: x.get("last_seen", ""), 
                               reverse=True)
        
        for i, session in enumerate(sorted_sessions[:limit]):
            print(f"{i+1}. Session ID: {session['id']}")
            print(f"   トレース数: {session['trace_count']}")
            print(f"   最初の入力: {session['first_input']}...")
            
            # タイムスタンプをパース
            try:
                if session['first_seen']:
                    first_time = datetime.fromisoformat(
                        session['first_seen'].replace('Z', '+00:00')
                    )
                    print(f"   開始時刻: {first_time.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                print(f"   開始時刻: {session['first_seen']}")
            
            print("-" * 60)
    else:
        print(f"エラー: {response.status_code}")
        print(response.text)

def get_session_details(session_id):
    """特定のセッションの詳細を表示"""
    
    loader = ConversationHistoryLoader()
    traces = loader.get_session_traces(session_id)
    
    if traces:
        print(f"\n=== セッション {session_id} の詳細 ===")
        print(f"トレース数: {len(traces)}")
        
        # 会話の流れを表示
        print("\n会話の流れ:")
        for i, trace in enumerate(traces):
            input_text = str(trace.get("input", ""))[:50]
            output_text = str(trace.get("output", ""))[:50]
            agent_name = trace.get("name", "Unknown")
            
            print(f"\n{i+1}. [{agent_name}]")
            if input_text:
                print(f"   入力: {input_text}...")
            if output_text:
                print(f"   出力: {output_text}...")
    else:
        print(f"セッション {session_id} が見つかりません")

if __name__ == "__main__":
    # 最近のセッションを表示
    list_recent_sessions()
    
    # 特定のセッションの詳細を見たい場合
    try:
        session_id = input("\n詳細を見たいセッションIDを入力（Enterでスキップ）: ").strip()
        if session_id:
            get_session_details(session_id)
    except EOFError:
        # バッチ実行の場合は入力をスキップ
        pass