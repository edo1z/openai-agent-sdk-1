"""
Observationの詳細な構造を確認
"""
from conversation_history import ConversationHistoryLoader
import json

def analyze_observation_structure(session_id: str):
    """Observationの完全な構造を分析"""
    
    loader = ConversationHistoryLoader()
    observations = loader.get_session_observations(session_id)
    
    print(f"Total observations: {len(observations)}")
    
    # 各タイプのObservationを1つずつ詳しく見る
    seen_types = set()
    
    for obs in observations:
        obs_type = obs.get('type')
        obs_name = obs.get('name', '')
        
        type_name_key = f"{obs_type}:{obs_name}"
        
        if type_name_key not in seen_types:
            seen_types.add(type_name_key)
            
            print(f"\n{'='*60}")
            print(f"Type: {obs_type}, Name: {obs_name}")
            print(f"{'='*60}")
            
            # 主要なフィールドを表示
            for key in ['id', 'traceId', 'type', 'name', 'startTime', 'endTime', 
                       'model', 'modelParameters', 'input', 'output', 'metadata',
                       'usage', 'level', 'statusMessage', 'parentObservationId',
                       'version', 'projectId', 'promptTokens', 'completionTokens',
                       'totalTokens', 'unit', 'inputCost', 'outputCost', 'totalCost',
                       'completionStartTime']:
                
                if key in obs:
                    value = obs[key]
                    if value is not None:
                        if isinstance(value, (dict, list)) and len(str(value)) > 100:
                            print(f"{key}: {type(value).__name__} (length: {len(value) if isinstance(value, list) else 'dict'})")
                            # 最初の要素/キーだけ表示
                            if isinstance(value, list) and value:
                                print(f"  First item: {str(value[0])[:100]}...")
                            elif isinstance(value, dict):
                                print(f"  Keys: {list(value.keys())[:5]}")
                        else:
                            print(f"{key}: {value}")
            
            # 全てのキーを表示（見逃しているものがないか確認）
            all_keys = set(obs.keys())
            standard_keys = {'id', 'traceId', 'type', 'name', 'startTime', 'endTime',
                           'model', 'modelParameters', 'input', 'output', 'metadata',
                           'usage', 'level', 'statusMessage', 'parentObservationId',
                           'version', 'projectId', 'promptTokens', 'completionTokens',
                           'totalTokens', 'unit', 'inputCost', 'outputCost', 'totalCost',
                           'completionStartTime'}
            
            extra_keys = all_keys - standard_keys
            if extra_keys:
                print(f"\nExtra keys found: {extra_keys}")


if __name__ == "__main__":
    session_id = "d73a44e0-c425-4eac-b853-55a2ff1b1444"
    analyze_observation_structure(session_id)