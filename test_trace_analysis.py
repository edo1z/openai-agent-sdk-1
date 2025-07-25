"""
Langfuseのトレースデータ構造を詳しく分析するスクリプト
"""
import json
from conversation_history import ConversationHistoryLoader

def analyze_trace_structure():
    """トレースデータの構造を分析"""
    
    loader = ConversationHistoryLoader()
    
    # セッションIDを入力
    session_id = input("分析するセッションIDを入力してください: ").strip()
    
    if not session_id:
        print("セッションIDが入力されませんでした")
        return
    
    traces = loader.get_session_traces(session_id)
    
    if not traces:
        print("トレースが見つかりませんでした")
        return
    
    print(f"\n=== {len(traces)} 個のトレースを取得 ===\n")
    
    # 各トレースの構造を詳しく表示
    for i, trace in enumerate(traces[:3]):  # 最初の3つを詳しく見る
        print(f"--- トレース {i+1} ---")
        print(f"ID: {trace.get('id')}")
        print(f"Timestamp: {trace.get('timestamp')}")
        print(f"Name: {trace.get('name')}")
        print(f"Session ID: {trace.get('sessionId')}")
        
        # inputの構造
        if 'input' in trace:
            print(f"\nInput type: {type(trace['input'])}")
            if isinstance(trace['input'], dict):
                print(f"Input keys: {list(trace['input'].keys())}")
            print(f"Input content: {str(trace['input'])[:200]}...")
        
        # outputの構造
        if 'output' in trace:
            print(f"\nOutput type: {type(trace['output'])}")
            if isinstance(trace['output'], dict):
                print(f"Output keys: {list(trace['output'].keys())}")
            print(f"Output content: {str(trace['output'])[:200]}...")
        
        # その他のフィールド
        other_keys = [k for k in trace.keys() if k not in ['id', 'timestamp', 'name', 'sessionId', 'input', 'output']]
        if other_keys:
            print(f"\nその他のフィールド: {other_keys}")
            for key in other_keys[:5]:  # 最初の5つ
                value = trace[key]
                if isinstance(value, (dict, list)):
                    print(f"  {key}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"  {key}: {str(value)[:100]}...")
        
        print("\n" + "="*50 + "\n")
    
    # 全トレースの名前を確認（エージェントの種類を見る）
    print("=== 全トレースの名前一覧 ===")
    trace_names = {}
    for trace in traces:
        name = trace.get('name', 'Unknown')
        trace_names[name] = trace_names.get(name, 0) + 1
    
    for name, count in trace_names.items():
        print(f"{name}: {count}回")

if __name__ == "__main__":
    analyze_trace_structure()