"""
セッションIDのフィルタリングが正しく機能しているか確認
"""
from conversation_history import ConversationHistoryLoader

def analyze_session_filtering(session_id: str):
    """セッションIDフィルタリングの問題を分析"""
    
    loader = ConversationHistoryLoader()
    
    # 1. Observations APIの応答を確認
    observations = loader.get_session_observations(session_id)
    
    print(f"取得したobservations数: {len(observations)}")
    
    # 各observationのtraceIdとセッションIDを確認
    trace_sessions = {}
    
    for obs in observations:
        trace_id = obs.get("traceId")
        # observationにsessionIdがあるか確認
        obs_session_id = obs.get("sessionId")
        
        if trace_id not in trace_sessions:
            trace_sessions[trace_id] = {
                "session_id": obs_session_id,
                "count": 0,
                "types": set()
            }
        
        trace_sessions[trace_id]["count"] += 1
        trace_sessions[trace_id]["types"].add(obs.get("type"))
    
    print(f"\n異なるトレース数: {len(trace_sessions)}")
    
    # トレースごとのセッションIDを確認
    print("\nトレースごとのセッションID:")
    for i, (trace_id, info) in enumerate(list(trace_sessions.items())[:10]):
        print(f"{i+1}. Trace: {trace_id[:8]}...")
        print(f"   SessionID in observation: {info['session_id']}")
        print(f"   Observation count: {info['count']}")
        print(f"   Types: {info['types']}")
    
    # 2. 各トレースの詳細を取得してセッションIDを確認
    print("\n\nトレース詳細からセッションIDを確認:")
    traces = loader.get_session_traces(session_id)
    
    print(f"Traces APIで取得したトレース数: {len(traces)}")
    
    for i, trace in enumerate(traces[:5]):
        print(f"\n{i+1}. Trace ID: {trace.get('id')[:8]}...")
        print(f"   SessionID: {trace.get('sessionId')}")
        print(f"   Name: {trace.get('name')}")
    
    # 3. 実際に問題のあるセッションIDを確認
    print(f"\n\n=== 問題の分析 ===")
    print(f"指定したセッションID: {session_id}")
    
    # GENERATIONタイプのobservationを詳しく見る
    generation_count = 0
    for obs in observations:
        if obs.get("type") == "GENERATION":
            generation_count += 1
            if generation_count <= 3:  # 最初の3つだけ
                print(f"\nGENERATION {generation_count}:")
                print(f"  TraceId: {obs.get('traceId')[:8]}...")
                print(f"  StartTime: {obs.get('startTime')}")
                
                # inputの中身を確認
                input_data = obs.get("input", [])
                if isinstance(input_data, list) and input_data:
                    msg_count = len([m for m in input_data if isinstance(m, dict) and m.get("role") != "system"])
                    print(f"  メッセージ数（システム除く）: {msg_count}")


if __name__ == "__main__":
    session_id = "d73a44e0-c425-4eac-b853-55a2ff1b1444"
    analyze_session_filtering(session_id)