# OpenAI Agents SDK - セッション永続化の探求

## 背景

OpenAI Agents SDKを使用してチャットシステムを構築する際、会話の中断・再開機能は重要な要件でした。
当初、「Langfuseから会話履歴を復元する」というお題から始まりました。

### 参考リンク
- [Langfuse - OpenAI Agents統合ガイド](https://langfuse.com/integrations/frameworks/openai-agents)
- [OpenAI Agents - カスタムセッション実装](https://openai.github.io/openai-agents-python/sessions/#custom-memory-implementations)

## やってみたこと

### 1. Langfuse APIを使った会話履歴の取得（初期アプローチ）

最初に、[Langfuse統合](https://langfuse.com/integrations/frameworks/openai-agents)でログが自動保存されているデータから、`/api/public/observations`エンドポイントを使用して、sessionIdで会話履歴を取得しようとしました。

### 2. API制限の発見

observations APIの制限が判明：
- `/api/public/observations?sessionId=xxx`は、sessionIdでのフィルタリングに対応していない
- 全データから最新100件を返すだけで、指定したセッションのデータのみを取得できない

### 3. Langfuse APIドキュメントの調査

公式ドキュメントとGitHubディスカッションを調査した結果：
- **observations APIは直接sessionIdでのフィルタリングをサポートしていない**
- 推奨される回避策：traces経由でobservationsを取得
- これにより、N+1問題が発生（トレースごとにobservationsを取得）

### 4. API最適化の試み

複数のアプローチを試行：
- 試行1：`/api/public/observations?sessionId=xxx`（sessionIdフィルタが効かず失敗）
- 試行2：N+1 API呼び出し
  1. `/api/public/traces?sessionId=xxx`でセッションのトレース一覧を取得
  2. 各トレースに対して`/api/public/observations?traceId=xxx`でobservationsを取得
  3. 取得した全observationsから会話履歴を構築
- 結論：Langfuse APIの制限により、N+1問題は避けられない

### 5. データ構造の課題

Langfuseのデータ構造は複雑で多様：
- logfire instrumentationによる特殊なデータ形式
- GENERATIONタイプのinputフィールドに累積的な会話履歴
- OpenAI API v2形式への対応（`type: "output_text"`）
- scrubbingによるデータマスキング問題

## やってみた結果・学んだこと

### 技術的な学び

1. **Langfuse APIの制約**
   - sessionIdでの直接フィルタリングが不可能
   - API制限（limit最大100）
   - データ取得の遅延（15-30秒）

2. **データ構造の複雑性**
   - Langfuseとagents SDKのSessionの構造が根本的に異なる
   - 保存方法によってデータ形式が変わる（多様性の問題）
   - 復元時の変換処理が複雑

3. **パフォーマンスの観点**
   - Langfuse API経由：複数回のHTTPリクエスト
   - Redis直接アクセス：単一の高速アクセス

### 根本的な気づき

**「そもそもSessionを消さずにそのまま使うのが圧倒的にシンプルで確実」**

この気づきから、アプローチを大きく転換しました。

## 最終的な解決策：RedisSession

### なぜRedisか

1. **SQLiteの限界**
   - ローカルファイルベースでスケールが困難
   - 分散環境での共有が不可能

2. **Redisの利点**
   - クラウド対応（Redis Cloud、AWS ElastiCache、Upstash等）
   - 高速なインメモリアクセス
   - TTL（有効期限）の自動管理
   - 分散環境でのセッション共有

### 実装の成果

[OpenAI Agents SDKのSession protocol](https://openai.github.io/openai-agents-python/sessions/#custom-memory-implementations)に準拠したRedisSession実装により：

- **シンプル**: セッションIDだけで完全復元
- **高速**: 直接的なデータアクセス
- **スケーラブル**: クラウド環境での水平スケール対応
- **確実**: データ構造の変換不要、そのまま保存・復元

## 結論

Langfuseは優れた観測ツールですが、セッション永続化のためのストレージとしてはAPIの制限や速度の課題などがあるかなと思いました。今回の場合は、専用のセッションストレージ（Redis）を使用することで、よりシンプルで確実、かつスケーラブルな解決策を実現できました。

