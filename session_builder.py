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

        # Langfuseから履歴を取得
        loader = ConversationHistoryLoader()
        traces = loader.get_session_traces(session_id)

        if not traces:
            print("過去の会話が見つかりませんでした")
            return session

        # 会話履歴を抽出
        conversation = loader.extract_conversation_history(traces)

        # 会話履歴をSessionに追加
        items_to_add = []
        for msg in conversation:
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
                                "type": "output_text",
                                "annotations": [],
                                "logprobs": [],
                            }
                        ],
                        "type": "message",
                        "status": "complete",
                        "id": f"msg_{len(items_to_add)}",  # 仮のID
                    }
                )

        # セッションに履歴を追加
        if items_to_add:
            await session.add_items(items_to_add)
            print(
                f"セッション {session_id} に {len(items_to_add)} 個のメッセージを復元しました"
            )

        return session

