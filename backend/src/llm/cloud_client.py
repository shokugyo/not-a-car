import json
import time
import httpx
from typing import Optional, AsyncGenerator

from src.config import Settings, get_settings
from .base import BaseLLMClient, LLMProvider


class QwenCloudClient(BaseLLMClient):
    """Alibaba Cloud Qwen API クライアント（OpenAI互換API）"""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._settings.qwen_timeout)
        return self._client

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.CLOUD

    @property
    def is_available(self) -> bool:
        return bool(self._settings.qwen_api_key)

    @property
    def model_name(self) -> str:
        return self._settings.qwen_model

    @property
    def model_name_fast(self) -> str:
        return self._settings.qwen_model_fast

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
            model: 使用するモデル（デフォルト: qwen_model）
            temperature: 温度パラメータ
            max_tokens: 最大トークン数

        Returns:
            アシスタントのレスポンステキスト
        """
        if not self.is_available:
            raise RuntimeError("Qwen API key is not configured")

        model = model or self._settings.qwen_model
        temperature = temperature if temperature is not None else self._settings.qwen_temperature
        max_tokens = max_tokens or self._settings.qwen_max_tokens

        headers = {
            "Authorization": f"Bearer {self._settings.qwen_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = await self.client.post(
            f"{self._settings.qwen_api_base}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_fast(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> str:
        """高速・低コストモデルでチャット補完を実行"""
        return await self.chat(
            messages=messages,
            model=self._settings.qwen_model_fast,
            temperature=temperature,
        )

    async def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        ストリーミングでチャット補完を実行

        Args:
            messages: メッセージリスト
            model: 使用するモデル（デフォルト: qwen_model）
            temperature: 温度パラメータ

        Yields:
            生成されたトークン
        """
        if not self.is_available:
            raise RuntimeError("Qwen API key is not configured")

        model = model or self._settings.qwen_model
        temperature = temperature if temperature is not None else self._settings.qwen_temperature

        headers = {
            "Authorization": f"Bearer {self._settings.qwen_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        async with self.client.stream(
            "POST",
            f"{self._settings.qwen_api_base}/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> dict:
        """ヘルスチェックを実行"""
        if not self.is_available:
            return {
                "healthy": False,
                "latency_ms": 0,
                "error": "API key not configured",
            }

        try:
            start = time.time()
            await self.chat(
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            latency = (time.time() - start) * 1000

            return {
                "healthy": True,
                "latency_ms": round(latency, 2),
                "error": None,
            }
        except Exception as e:
            return {
                "healthy": False,
                "latency_ms": 0,
                "error": str(e),
            }

    async def close(self):
        """クライアントを閉じる"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
