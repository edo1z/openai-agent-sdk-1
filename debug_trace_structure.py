"""
Langfuseのトレース構造を詳しく調査
"""
import json
from conversation_history import ConversationHistoryLoader


def debug_trace_structure(session_id: str):
    """トレースの実際の構造を詳しく表示"""
    
    loader = ConversationHistoryLoader()
    traces = loader.get_session_traces(session_id)
    
    print(f"\n=== セッション {session_id} のトレース分析 ===")
    print(f"取得したトレース数: {len(traces)}")
    
    if not traces:
        print("トレースが見つかりませんでした")
        return
    
    # 各トレースの構造を詳しく分析
    for i, trace in enumerate(traces):
        print(f"\n--- トレース {i+1}/{len(traces)} ---")
        print(f"ID: {trace.get('id', 'N/A')}")
        print(f"Name: {trace.get('name', 'N/A')}")
        print(f"Timestamp: {trace.get('timestamp', 'N/A')}")
        
        # すべてのキーを表示
        print(f"利用可能なキー: {list(trace.keys())}")
        
        # inputの詳細
        if 'input' in trace:
            input_data = trace['input']
            print(f"\nInput:")
            print(f"  Type: {type(input_data).__name__}")
            if input_data is None:
                print(f"  Value: None")
            elif isinstance(input_data, str):
                print(f"  Value: {input_data[:100]}...")
            elif isinstance(input_data, dict):
                print(f"  Keys: {list(input_data.keys())}")
                print(f"  Sample: {str(input_data)[:100]}...")
            elif isinstance(input_data, list):
                print(f"  Length: {len(input_data)}")
                print(f"  First item: {str(input_data[0])[:100] if input_data else 'Empty'}...")
        
        # outputの詳細
        if 'output' in trace:
            output_data = trace['output']
            print(f"\nOutput:")
            print(f"  Type: {type(output_data).__name__}")
            if output_data is None:
                print(f"  Value: None")
            elif isinstance(output_data, str):
                print(f"  Value: {output_data[:100]}...")
            elif isinstance(output_data, dict):
                print(f"  Keys: {list(output_data.keys())}")
                print(f"  Sample: {str(output_data)[:100]}...")
            elif isinstance(output_data, list):
                print(f"  Length: {len(output_data)}")
                print(f"  First item: {str(output_data[0])[:100] if output_data else 'Empty'}...")
        
        # その他の重要なフィールド
        if 'events' in trace:
            print(f"\nEvents: {len(trace['events'])} events")
        if 'spans' in trace:
            print(f"Spans: {len(trace['spans'])} spans")
        if 'observations' in trace:
            print(f"Observations: {len(trace['observations'])} observations")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    # セッションIDを入力
    session_id = input("分析するセッションIDを入力: ").strip()
    if session_id:
        debug_trace_structure(session_id)
    else:
        # テスト用のセッションID
        debug_trace_structure("02c71b00-ea74-4621-92bf-96b5dea89625")