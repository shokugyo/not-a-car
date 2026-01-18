import logging
from typing import Optional, AsyncGenerator

from .base import BaseLLMClient, LLMProvider
from .mock_client import MockLLMClient

logger = logging.getLogger(__name__)


class FallbackLLMClient(BaseLLMClient):
    """フォールバックチェーン付きLLMクライアント"""

    def __init__(self, clients: list[BaseLLMClient]):
        """
        Args:
            clients: フォールバック順のクライアントリスト
        """
        if not clients:
            clients = [MockLLMClient()]

        self._clients = clients
        self._active_client: BaseLLMClient = clients[0]
        self._failed_providers: set[str] = set()

    @property
    def provider(self) -> LLMProvider:
        return self._active_client.provider

    @property
    def is_available(self) -> bool:
        return self._active_client.is_available

    @property
    def model_name(self) -> str:
        return self._active_client.model_name

    @property
    def model_name_fast(self) -> str:
        return self._active_client.model_name_fast

    @property
    def active_client(self) -> BaseLLMClient:
        return self._active_client

    @property
    def all_clients(self) -> list[BaseLLMClient]:
        return self._clients

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """フォールバック付きでチャット補完を実行"""
        last_error: Optional[Exception] = None

        for client in self._clients:
            if client.provider.value in self._failed_providers:
                continue

            try:
                result = await client.chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                self._active_client = client
                return result

            except Exception as e:
                logger.warning(
                    f"Provider {client.provider.value} failed: {e}, "
                    f"trying next provider"
                )
                last_error = e
                self._failed_providers.add(client.provider.value)
                continue

        # 全プロバイダーが失敗した場合、失敗フラグをリセットして再試行
        if last_error:
            logger.error(f"All providers failed, resetting and using mock")
            self._failed_providers.clear()
            mock = MockLLMClient()
            return await mock.chat(messages)

        raise RuntimeError("No LLM clients available")

    async def chat_fast(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> str:
        """フォールバック付きで高速チャット補完を実行"""
        last_error: Optional[Exception] = None

        for client in self._clients:
            if client.provider.value in self._failed_providers:
                continue

            try:
                result = await client.chat_fast(
                    messages=messages,
                    temperature=temperature,
                )
                self._active_client = client
                return result

            except Exception as e:
                logger.warning(
                    f"Provider {client.provider.value} failed (fast): {e}, "
                    f"trying next provider"
                )
                last_error = e
                self._failed_providers.add(client.provider.value)
                continue

        if last_error:
            logger.error(f"All providers failed (fast), resetting and using mock")
            self._failed_providers.clear()
            mock = MockLLMClient()
            return await mock.chat_fast(messages)

        raise RuntimeError("No LLM clients available")

    async def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """フォールバック付きでストリーミングチャット補完を実行"""
        last_error: Optional[Exception] = None

        for client in self._clients:
            if client.provider.value in self._failed_providers:
                continue

            try:
                async for token in client.chat_stream(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                ):
                    self._active_client = client
                    yield token
                return  # 成功したら終了

            except Exception as e:
                logger.warning(
                    f"Provider {client.provider.value} failed (stream): {e}, "
                    f"trying next provider"
                )
                last_error = e
                self._failed_providers.add(client.provider.value)
                continue

        if last_error:
            logger.error(f"All providers failed (stream), resetting and using mock")
            self._failed_providers.clear()
            mock = MockLLMClient()
            async for token in mock.chat_stream(messages):
                yield token
            return

        raise RuntimeError("No LLM clients available")

    async def health_check(self) -> dict:
        """全クライアントのヘルスチェックを実行"""
        results = {}

        for client in self._clients:
            health = await client.health_check()
            results[client.provider.value] = health

        # アクティブクライアントの情報を追加
        active_health = results.get(self._active_client.provider.value, {})

        return {
            "active_provider": self._active_client.provider.value,
            "healthy": active_health.get("healthy", False),
            "latency_ms": active_health.get("latency_ms", 0),
            "error": active_health.get("error"),
            "providers": results,
            "failed_providers": list(self._failed_providers),
        }

    async def close(self):
        """全クライアントを閉じる"""
        for client in self._clients:
            await client.close()

    def get_status(self) -> dict:
        """拡張ステータス情報"""
        return {
            "active_provider": self._active_client.provider.value,
            "active_model": self._active_client.model_name,
            "available_providers": [c.provider.value for c in self._clients],
            "failed_providers": list(self._failed_providers),
        }

    def reset_failures(self):
        """失敗フラグをリセット"""
        self._failed_providers.clear()
        self._active_client = self._clients[0]
