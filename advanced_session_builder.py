"""
複数エージェントとhandoffに対応した高度なセッション復元
"""
from typing import List, Dict, Any
from agents import SQLiteSession, HandoffOutputItem, Agent
from conversation_history import ConversationHistoryLoader


class AdvancedSessionBuilder:
    """複数エージェントシステムに対応したセッション復元"""
    
    @staticmethod
    async def rebuild_from_langfuse_advanced(session_id: str) -> SQLiteSession:
        """Langfuseから詳細な会話履歴を復元"""
        
        # インメモリのSQLiteSessionを作成
        session = SQLiteSession(session_id)
        
        # Langfuseから履歴を取得
        loader = ConversationHistoryLoader()
        traces = loader.get_session_traces(session_id)
        
        if not traces:
            print("過去の会話が見つかりませんでした")
            return session
        
        # より詳細な履歴抽出
        items_to_add = []
        
        for trace in traces:
            # トレース名からエージェントを識別
            trace_name = trace.get('name', '')
            
            # ユーザー入力の処理
            if 'input' in trace:
                input_data = trace['input']
                
                # inputが文字列の場合（ユーザーメッセージ）
                if isinstance(input_data, str):
                    items_to_add.append({
                        "role": "user",
                        "content": input_data
                    })
                
                # inputが辞書の場合（詳細な構造）
                elif isinstance(input_data, dict):
                    # メッセージやコンテンツを探す
                    content = (input_data.get('content') or 
                             input_data.get('message') or 
                             input_data.get('query') or
                             str(input_data))
                    
                    items_to_add.append({
                        "role": "user",
                        "content": content
                    })
            
            # エージェント出力の処理
            if 'output' in trace:
                output_data = trace['output']
                
                # outputが文字列の場合
                if isinstance(output_data, str):
                    items_to_add.append({
                        "role": "assistant",
                        "content": [{
                            "text": output_data,
                            "type": "output_text",
                            "annotations": [],
                            "logprobs": []
                        }],
                        "type": "message",
                        "status": "complete",
                        "id": f"msg_{len(items_to_add)}",
                        "agent_name": trace_name  # エージェント名を保持
                    })
                
                # outputが辞書の場合（handoffを含む可能性）
                elif isinstance(output_data, dict):
                    # handoffの検出
                    if 'handoff' in output_data or 'transfer' in output_data:
                        # Handoffアイテムとして追加
                        handoff_info = {
                            "type": "handoff",
                            "from_agent": trace_name,
                            "to_agent": output_data.get('handoff_to', 'unknown'),
                            "reason": output_data.get('reason', ''),
                            "timestamp": trace.get('timestamp')
                        }
                        items_to_add.append(handoff_info)
                    
                    # 通常のメッセージ
                    else:
                        content = (output_data.get('content') or 
                                 output_data.get('message') or 
                                 output_data.get('response') or
                                 str(output_data))
                        
                        items_to_add.append({
                            "role": "assistant",
                            "content": [{
                                "text": content,
                                "type": "output_text",
                                "annotations": [],
                                "logprobs": []
                            }],
                            "type": "message",
                            "status": "complete",
                            "id": f"msg_{len(items_to_add)}",
                            "agent_name": trace_name
                        })
        
        # セッションに履歴を追加（handoffは除外）
        filtered_items = [item for item in items_to_add if item.get('type') != 'handoff']
        
        if filtered_items:
            await session.add_items(filtered_items)
            print(f"セッション {session_id} に {len(filtered_items)} 個のメッセージを復元しました")
            
            # handoff情報もログとして表示
            handoffs = [item for item in items_to_add if item.get('type') == 'handoff']
            if handoffs:
                print(f"検出されたhandoff: {len(handoffs)}回")
                for h in handoffs:
                    print(f"  {h['from_agent']} -> {h['to_agent']}")
        
        return session
    
    @staticmethod
    def extract_agent_flow(traces: List[Dict]) -> List[Dict[str, Any]]:
        """トレースからエージェントのフローを抽出"""
        flow = []
        
        for trace in traces:
            agent_name = trace.get('name', 'Unknown')
            timestamp = trace.get('timestamp')
            
            flow_item = {
                'agent': agent_name,
                'timestamp': timestamp,
                'input_summary': str(trace.get('input', ''))[:50],
                'output_summary': str(trace.get('output', ''))[:50]
            }
            
            flow.append(flow_item)
        
        return flow