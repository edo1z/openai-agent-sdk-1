# LangfuseでSession IDを確認する方法

## 1. Traces画面から確認

1. Langfuseにログイン
2. 左側メニューから「Traces」をクリック
3. トレース一覧が表示される

### Session IDの表示場所：

- **一覧画面**: 各トレースの行に「Session」列がある場合、そこにSession IDが表示
- **詳細画面**: トレースをクリックして詳細を開くと、右側のメタデータセクションに以下が表示：
  - `Session ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
  - または「Session」フィールド

## 2. Sessions画面から確認（推奨）

1. 左側メニューから「Sessions」をクリック
2. セッション一覧が表示される
3. 各セッションのIDが表示される

### セッションの詳細：
- セッションをクリックすると、そのセッションに含まれる全てのトレースが表示
- 上部にSession IDが大きく表示される

## 3. コード内でSession IDを確認

main.pyを実行すると：
```
セッションを終了します。
セッションID: 123e4567-e89b-12d3-a456-426614174000
このIDを使用して、main_with_resume.pyで会話を再開できます。
```

## 4. APIで確認

以下のスクリプトで最近のセッションを一覧表示：

```python
from conversation_history import ConversationHistoryLoader
import httpx

loader = ConversationHistoryLoader()

# Sessions APIエンドポイント
url = f"{loader.host}/api/public/sessions"

response = httpx.get(
    url,
    headers={
        "Authorization": loader.auth_header,
        "Content-Type": "application/json"
    },
    params={"limit": 10}  # 最新10件
)

if response.status_code == 200:
    sessions = response.json().get("data", [])
    for session in sessions:
        print(f"Session ID: {session['id']}")
        print(f"Created: {session.get('createdAt')}")
        print(f"Traces: {session.get('countTraces', 0)}")
        print("-" * 40)
```

## トラブルシューティング

Session IDが表示されない場合：
1. コードでSQLiteSessionにsession_idを正しく設定しているか確認
2. Langfuse統合が正しく設定されているか確認（環境変数など）
3. トレースが実際にLangfuseに送信されているか確認