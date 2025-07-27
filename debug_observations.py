"""
observations内のデータ構造を詳しく調査
"""
from conversation_history import ConversationHistoryLoader


def debug_observations(session_id: str):
    """observationsの詳細を表示"""
    
    loader = ConversationHistoryLoader()
    traces = loader.get_session_traces(session_id)
    
    if not traces:
        print("トレースが見つかりませんでした")
        return
    
    # 最初のトレースのobservationsを詳しく見る
    trace = traces[0]
    observations = trace.get("observations", [])
    
    print(f"\n=== トレース {trace.get('id')} のobservations分析 ===")
    print(f"Observations数: {len(observations)}")
    
    for i, obs in enumerate(observations):
        print(f"\n--- Observation {i+1}/{len(observations)} ---")
        print(f"Type of obs: {type(obs).__name__}")
        
        if isinstance(obs, str):
            print(f"String value: {obs}")
            continue
            
        print(f"ID: {obs.get('id', 'N/A')}")
        print(f"Type: {obs.get('type', 'N/A')}")
        print(f"Name: {obs.get('name', 'N/A')}")
        print(f"Start Time: {obs.get('startTime', 'N/A')}")
        
        # 利用可能なキー
        print(f"Keys: {list(obs.keys())}")
        
        # inputの内容
        if 'input' in obs and obs['input']:
            print(f"\nInput:")
            input_data = obs['input']
            if isinstance(input_data, str):
                print(f"  String: {input_data[:200]}...")
            elif isinstance(input_data, dict):
                print(f"  Dict keys: {list(input_data.keys())}")
                for key, value in list(input_data.items())[:3]:
                    print(f"    {key}: {str(value)[:100]}...")
            elif isinstance(input_data, list):
                print(f"  List length: {len(input_data)}")
                if input_data:
                    print(f"  First item: {str(input_data[0])[:100]}...")
        
        # outputの内容
        if 'output' in obs and obs['output']:
            print(f"\nOutput:")
            output_data = obs['output']
            if isinstance(output_data, str):
                print(f"  String: {output_data[:200]}...")
            elif isinstance(output_data, dict):
                print(f"  Dict keys: {list(output_data.keys())}")
                for key, value in list(output_data.items())[:3]:
                    print(f"    {key}: {str(value)[:100]}...")
            elif isinstance(output_data, list):
                print(f"  List length: {len(output_data)}")
                if output_data:
                    print(f"  First item: {str(output_data[0])[:100]}...")
        
        # メタデータ
        if 'metadata' in obs:
            print(f"\nMetadata: {obs['metadata']}")


if __name__ == "__main__":
    session_id = input("分析するセッションIDを入力: ").strip()
    if session_id:
        debug_observations(session_id)
    else:
        debug_observations("02c71b00-ea74-4621-92bf-96b5dea89625")