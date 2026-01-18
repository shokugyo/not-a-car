from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from enum import Enum


class LLMProvider(str, Enum):
    """LLMプロバイダーの種類"""
    CLOUD = "cloud"
    LOCAL = "local"
    MOCK = "mock"
    AUTO = "auto"


class BaseLLMClient(ABC):
    """LLMクライアントの抽象基底クラス"""

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """プロバイダー種類を返す"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """クライアントが利用可能かどうか"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """使用中のモデル名"""
        pass

    @property
    @abstractmethod
    def model_name_fast(self) -> str:
        """高速モデル名"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        チャット補完を実行

        Args:
            messages: メッセージリスト [{"role": "system", "content": "..."}, ...]
            model: 使用するモデル
            temperature: 温度パラメータ
            max_tokens: 最大トークン数

        Returns:
            アシスタントのレスポンステキスト
        """
        pass

    @abstractmethod
    async def chat_fast(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> str:
        """高速・低コストモデルでチャット補完を実行"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        ストリーミングでチャット補完を実行

        Args:
            messages: メッセージリスト [{"role": "system", "content": "..."}, ...]
            model: 使用するモデル
            temperature: 温度パラメータ

        Yields:
            生成されたトークン（文字列）
        """
        pass
        yield  # AsyncGeneratorとして認識させるため

    @abstractmethod
    async def health_check(self) -> dict:
        """
        ヘルスチェックを実行

        Returns:
            {"healthy": bool, "latency_ms": float, "error": Optional[str]}
        """
        pass

    @abstractmethod
    async def close(self):
        """クライアントを閉じる"""
        pass

    def get_status(self) -> dict:
        """ステータス情報を返す"""
        return {
            "provider": self.provider.value,
            "available": self.is_available,
            "model": self.model_name,
            "model_fast": self.model_name_fast,
        }
