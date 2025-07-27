"""
LangfuseのトレースからSQLiteSessionを再構築するユーティリティ
"""

from agents import SQLiteSession
from conversation_history import ConversationHistoryLoader


class SessionBuilder:
    """Langfuseのデータからインメモリ SQLiteSessionを再構築"""

    @staticmethod
    async def rebuild_from_langfuse(session_id: str) -> SQLiteSession:
        """Langfuseから会話履歴を取得してインメモリSessionに復元"""

        # インメモリのSQLiteSessionを作成
        session = SQLiteSession(session_id)

        # Langfuseから履歴を取得（1回のAPI呼び出し）
        loader = ConversationHistoryLoader()
        conversation = loader.extract_conversation_history_direct(session_id)

        if not conversation:
            print("過去の会話が見つかりませんでした")
            return session
        
        # デバッグ情報
        print(f"\n=== セッション復元デバッグ情報 ===")
        print(f"抽出したメッセージ数: {len(conversation)}")

        # 会話履歴をSessionに追加
        items_to_add = []
        for i, msg in enumerate(conversation):
            if msg["role"] == "user":
                # ユーザーメッセージは単純な辞書形式
                items_to_add.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                # アシスタントメッセージは複雑な構造を持つ
                items_to_add.append(
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "text": msg["content"],
                                "type": "text",  # "output_text"ではなく"text"を使用
                                "annotations": [],
                            }
                        ],
                        "type": "message",
                        "status": "complete",
                        "id": f"msg_{i}",  # 順序を保持
                    }
                )

        # セッションに履歴を追加
        if items_to_add:
            try:
                await session.add_items(items_to_add)
                print(f"✓ セッションに {len(items_to_add)} 個のメッセージを復元しました")
                
                # 復元されたアイテムを確認
                restored_items = await session.get_items()
                print(f"✓ セッション内の総アイテム数: {len(restored_items)}")
                
            except Exception as e:
                print(f"✗ セッション復元中にエラー: {e}")
                print(f"  エラーの詳細: {type(e).__name__}")

        return session

