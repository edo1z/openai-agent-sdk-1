"""
カスタムスクラビングの実装
"""
import re
from typing import Any
from logfire import ScrubbingOptions


def custom_scrub_callback(match: re.Match[str]) -> str:
    """カスタムスクラビングコールバック"""
    matched_text = match.group(0)
    
    # session_idの形式（UUID）の場合はスクラビングしない
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    if re.match(uuid_pattern, matched_text, re.IGNORECASE):
        return matched_text  # UUIDはそのまま返す
    
    # langfuse.session.id属性の値はスクラビングしない
    # これは属性レベルでの制御なので、ここでは対応できない可能性がある
    
    # その他の場合は通常のスクラビング
    if 'password' in matched_text.lower():
        return '[REDACTED-PASSWORD]'
    elif 'key' in matched_text.lower():
        return '[REDACTED-KEY]'
    elif 'token' in matched_text.lower():
        return '[REDACTED-TOKEN]'
    elif 'session' in matched_text.lower():
        # sessionを含むが、UUID形式でない場合のみスクラビング
        return '[REDACTED-SESSION]'
    
    return '[REDACTED]'


def get_custom_scrubbing_options() -> ScrubbingOptions:
    """カスタムスクラビングオプションを返す"""
    
    # デフォルトのパターンに加えて、追加のパターンを定義
    # ただし、session_idのようなUUID形式は除外したい
    
    return ScrubbingOptions(
        callback=custom_scrub_callback,
        # extra_patternsは追加でスクラビングしたいパターン
        extra_patterns=[
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+',  # APIキー
            r'password["\']?\s*[:=]\s*["\']?[\w-]+',     # パスワード
            # session_idはUUID形式なので、単純なsessionパターンは含めない
        ]
    )


# 別のアプローチ：環境変数で制御
def setup_scrubbing_allowlist():
    """スクラビングの許可リストを環境変数で設定"""
    import os
    
    # これらの環境変数が存在するかは不明だが、試してみる価値がある
    os.environ["LOGFIRE_SCRUBBING_ALLOWLIST"] = "session_id,session-id,sessionId"
    os.environ["LOGFIRE_SCRUBBING_EXCLUDE_ATTRIBUTES"] = "langfuse.session.id,langfuse.sessionId"
    os.environ["OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT"] = "1000000"  # 属性値の長さ制限を増やす