"""
会話履歴に重複がないか確認するテスト
"""
from conversation_history import ConversationHistoryLoader


def check_conversation_duplicates(session_id: str):
    """会話履歴の重複をチェック"""
    
    loader = ConversationHistoryLoader()
    
    # 1回のAPI呼び出しで履歴を取得
    conversation = loader.extract_conversation_history_direct(session_id)
    
    print(f"\n=== セッション {session_id} の分析 ===")
    print(f"総メッセージ数: {len(conversation)}")
    
    # 会話の内容を表示
    print("\n会話履歴:")
    for i, msg in enumerate(conversation):
        role = "USER" if msg["role"] == "user" else "ASST"
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"{i+1}. [{role}] {content}")
    
    # 連続する同じロールをチェック
    print("\n連続性チェック:")
    issues = []
    for i in range(1, len(conversation)):
        if conversation[i]["role"] == conversation[i-1]["role"]:
            issues.append(f"位置 {i} と {i+1}: 同じロール '{conversation[i]['role']}' が連続")
    
    if issues:
        print("問題が見つかりました:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ 会話の順序は正常です（user/assistant が交互）")
    
    # 会話のペア数を確認
    user_count = sum(1 for msg in conversation if msg["role"] == "user")
    assistant_count = sum(1 for msg in conversation if msg["role"] == "assistant")
    
    print(f"\nメッセージ数:")
    print(f"  ユーザー: {user_count}")
    print(f"  アシスタント: {assistant_count}")
    
    if abs(user_count - assistant_count) > 1:
        print("⚠️ ユーザーとアシスタントのメッセージ数が大きく異なります")


if __name__ == "__main__":
    session_id = input("チェックするセッションIDを入力: ").strip()
    if session_id:
        check_conversation_duplicates(session_id)
    else:
        # デフォルトのテスト
        check_conversation_duplicates("02c71b00-ea74-4621-92bf-96b5dea89625")