import logging
from typing import Optional

from src.config import Settings, get_settings
from .base import BaseLLMClient, LLMProvider
from .cloud_client import QwenCloudClient
from .ollama_client import OllamaClient
from .mock_client import MockLLMClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """LLMクライアントのファクトリークラス"""

    _instance: Optional[BaseLLMClient] = None
    _settings: Optional[Settings] = None

    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> BaseLLMClient:
        """
        LLMクライアントを作成

        Args:
            provider: プロバイダー種類（"cloud", "local", "mock", "auto"）
            settings: 設定オブジェクト

        Returns:
            BaseLLMClientの実装
        """
        settings = settings or get_settings()
        provider = provider or settings.llm_provider

        if provider == LLMProvider.CLOUD.value:
            return QwenCloudClient(settings)
        elif provider == LLMProvider.LOCAL.value:
            return OllamaClient(settings)
        elif provider == LLMProvider.MOCK.value:
            return MockLLMClient()
        elif provider == LLMProvider.AUTO.value:
            return cls._auto_select(settings)
        else:
            logger.warning(f"Unknown provider '{provider}', falling back to mock")
            return MockLLMClient()

    @classmethod
    def _auto_select(cls, settings: Settings) -> BaseLLMClient:
        """
        利用可能なプロバイダーを自動選択

        優先順位:
        1. Cloud (APIキーが設定されている場合)
        2. Local (Ollamaが起動している場合) - 同期チェックは行わない
        3. Mock (フォールバック)
        """
        # Cloud APIキーが設定されていれば優先
        if settings.qwen_api_key:
            logger.info("Auto-selected: cloud (API key configured)")
            return QwenCloudClient(settings)

        # Ollamaをデフォルトで試行（実際の可用性は使用時にチェック）
        logger.info("Auto-selected: local (no API key, trying Ollama)")
        return OllamaClient(settings)

    @classmethod
    async def create_async(
        cls,
        provider: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> BaseLLMClient:
        """
        LLMクライアントを非同期で作成（可用性チェック付き）

        Args:
            provider: プロバイダー種類
            settings: 設定オブジェクト

        Returns:
            BaseLLMClientの実装
        """
        settings = settings or get_settings()
        provider = provider or settings.llm_provider

        if provider == LLMProvider.AUTO.value:
            return await cls._auto_select_async(settings)

        return cls.create(provider, settings)

    @classmethod
    async def _auto_select_async(cls, settings: Settings) -> BaseLLMClient:
        """
        利用可能なプロバイダーを非同期で自動選択（可用性チェック付き）
        """
        # Cloud APIキーが設定されていれば優先
        if settings.qwen_api_key:
            logger.info("Auto-selected: cloud (API key configured)")
            return QwenCloudClient(settings)

        # Ollamaの可用性を非同期でチェック
        ollama = OllamaClient(settings)
        is_available = await ollama.check_availability()

        if is_available:
            logger.info("Auto-selected: local (Ollama available)")
            return ollama

        # Ollamaが利用不可ならクローズしてモックを返す
        await ollama.close()
        logger.info("Auto-selected: mock (no providers available)")
        return MockLLMClient()

    @classmethod
    def get_singleton(
        cls,
        settings: Optional[Settings] = None,
    ) -> BaseLLMClient:
        """
        シングルトンインスタンスを取得

        Args:
            settings: 設定オブジェクト

        Returns:
            BaseLLMClientの実装
        """
        if cls._instance is None:
            cls._instance = cls.create(settings=settings)
            cls._settings = settings
        return cls._instance

    @classmethod
    async def reset_singleton(cls):
        """シングルトンをリセット"""
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
            cls._settings = None
