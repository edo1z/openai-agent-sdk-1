# 専門家の設定
experts.yaml

# 基本仕様
- experts.yamlに応じた専門家エージェントの自動作成
- ユーザの発言に応じて最適な専門家エージェントが回答する(handoffsを使う)
- whileループで延々と繰り返せる
- exitで終了
- メッセージはsessionで自動保存（メモリセッション）
- Langfuseにログ送信

# 詳細仕様
- session IDはuuidを毎回自動生成する

# ローカル環境設定

```
uv venv
source .venv/bin/activate
uv pip install -r requirement.txt
cp .env.example .env
python main.py
```


