# OpenAI Agents SDK - 専門家エージェントシステム

## 概要
OpenAI Agents SDKを使用した専門家エージェントシステムです。複数の専門家エージェントを設定し、ユーザーの質問に応じて最適な専門家が回答します。

## 機能

### 基本機能
- experts.yamlに応じた専門家エージェントの自動作成
- ユーザの発言に応じて最適な専門家エージェントが回答する(handoffsを使う)
- whileループで延々と繰り返せる
- exitで終了
- Langfuseにログ送信

### セッション管理
- **SQLiteSession（ローカル）**: インメモリまたはファイルベースの会話履歴保存
- **RedisSession（推奨）**: クラウド対応の永続的な会話履歴保存
  - セッションの自動復元
  - TTL（有効期限）管理
  - スケーラブルな実装

### 詳細仕様
- session IDはuuidを毎回自動生成する（再開時は既存IDを使用）
- RedisSessionでは7日間のデフォルトTTL（設定可能）

## セットアップ

### 1. 環境構築

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
```

### 2. 環境変数の設定

`.env`ファイルを編集：

```bash
# 必須
OPENAI_API_KEY=your-openai-api-key

# Langfuse（オプション）
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_HOST=https://cloud.langfuse.com

# Redis（RedisSession使用時）
REDIS_URL=redis://localhost:6379
REDIS_SESSION_TTL=604800  # 7日間
```

### 3. Redisのセットアップ（RedisSession使用時）

ローカルRedis:
```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# または Homebrew (Mac)
brew install redis
brew services start redis
```

クラウドRedis:
- [Redis Cloud](https://redis.com/cloud/overview/)
- [AWS ElastiCache](https://aws.amazon.com/elasticache/)
- [Upstash](https://upstash.com/)

## 使い方

### SQLiteSession（ローカル）
```bash
python main.py
```

### RedisSession（推奨）
```bash
python main_redis.py
```

### セッションの再開
実行時にセッションIDを入力することで、過去の会話を復元できます：
```
既存のセッションを再開しますか？ セッションIDを入力（新規の場合はEnter）: d73a44e0-c425-4eac-b853-55a2ff1b1444
```

## テスト

RedisSessionのテスト:
```bash
python test_redis_session.py
```


