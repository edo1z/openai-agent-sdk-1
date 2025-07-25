import os
import logging
from typing import Optional
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

logger = logging.getLogger(__name__)


class LangfuseLogger:
    def __init__(self):
        self.langfuse = None
        self.enabled = False
        self._span_context = None
        self._trace_id = None
        self._turn_count = 0
        self._setup()

    def _setup(self):
        """Langfuseクライアントの初期化"""
        # 環境変数取得
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not all([secret_key, public_key]):
            logger.info("Langfuse keys not found. Logging disabled.")
            return

        try:
            from langfuse import Langfuse
            
            self.langfuse = Langfuse(
                secret_key=secret_key,
                public_key=public_key,
                host=host
            )

            # 接続チェック
            if self.langfuse.auth_check():
                self.enabled = True
                logger.info("Langfuse integration enabled")
            else:
                logger.warning("Langfuse authentication failed")

            # langfuse.openaiをインポート（OpenAI SDKのパッチ）
            try:
                import langfuse.openai
                logger.info("OpenAI SDK patched with Langfuse")
            except ImportError:
                logger.warning("langfuse.openai not available")

        except ImportError:
            logger.info("Langfuse not installed. Install with: pip install langfuse")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")

    def start_session(self, session_id: str, initial_input: Optional[str] = None):
        """新しいセッションを開始（トレースレベル）"""
        if not self.enabled or not self.langfuse:
            return

        try:
            # セッション全体のトレースとして開始
            self._span_context = self.langfuse.start_as_current_span(
                name="Expert Agent Conversation",
                input=initial_input or "Conversation started",
                metadata={
                    "session_id": session_id,
                    "type": "conversation"
                }
            )
            
            # コンテキストマネージャーに入る
            self._root_span = self._span_context.__enter__()
            
            # 現在のトレースIDを取得（利用可能な場合）
            if hasattr(self.langfuse, 'get_current_trace_id'):
                self._trace_id = self.langfuse.get_current_trace_id()
            
            # トレース属性を更新
            self.langfuse.update_current_trace(
                name="Expert Agent Conversation",
                session_id=session_id,
                tags=["expert-agent", "chat"]
            )
            
            self._turn_count = 0
            logger.debug(f"Started Langfuse session: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to start Langfuse session: {e}")

    def log_turn(self, user_input: str, agent_response: str, agent_name: str = "Expert Agent", conversation_history: Optional[str] = None):
        """1つの会話ターン（質問と応答のペア）を記録"""
        if not self.enabled or not self.langfuse:
            return

        try:
            self._turn_count += 1
            
            # 実際のLLMへの入力（会話履歴を含む場合がある）
            actual_input = conversation_history if conversation_history else user_input
            
            # Generationとして記録（LLMの入出力ペア）
            with self.langfuse.start_as_current_generation(
                name=f"Turn {self._turn_count}: {agent_name}",
                model="gpt-4",  # 実際のモデル名に置き換え可能
                input=actual_input,
                output=agent_response,
                metadata={
                    "user_message": user_input,
                    "agent_name": agent_name,
                    "turn_number": self._turn_count,
                    "message_lengths": {
                        "user": len(user_input),
                        "agent": len(agent_response)
                    }
                }
            ) as generation:
                pass
            
            logger.debug(f"Logged conversation turn {self._turn_count}")
        except Exception as e:
            logger.warning(f"Failed to log conversation turn: {e}")

    def end_session(self, total_turns: Optional[int] = None):
        """セッションを終了"""
        if not self.enabled or not self._span_context:
            return

        try:
            # ルートスパンを更新
            if self._root_span and hasattr(self._root_span, 'update'):
                self._root_span.update(
                    output=f"Conversation ended after {total_turns or self._turn_count} turns",
                    metadata={
                        "total_turns": total_turns or self._turn_count
                    }
                )
            
            # コンテキストマネージャーを終了
            self._span_context.__exit__(None, None, None)
            self.flush()
            logger.debug("Ended Langfuse session")
        except Exception as e:
            logger.warning(f"Failed to end Langfuse session: {e}")
        finally:
            self._span_context = None
            self._root_span = None
            self._trace_id = None

    def flush(self):
        """バッファされたイベントを送信"""
        if self.enabled and self.langfuse:
            try:
                self.langfuse.flush()
            except Exception as e:
                logger.warning(f"Failed to flush Langfuse: {e}")


# シングルトンインスタンス
langfuse_logger = LangfuseLogger()