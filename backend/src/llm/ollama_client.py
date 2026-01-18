import json
import time
import httpx
from typing import Optional, AsyncGenerator

from src.config import Settings, get_settings
from .base import BaseLLMClient, LLMProvider


class OllamaClient(BaseLLMClient):
    """Ollama ローカルLLMクライアント"""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None
        self._available: Optional[bool] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._settings.ollama_timeout)
        return self._client

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.LOCAL

    @property
    def is_available(self) -> bool:
        if self._available is None:
            return True
        return self._available

    @property
    def model_name(self) -> str:
        return self._settings.ollama_model

    @property
    def model_name_fast(self) -> str:
        return self._settings.ollama_model_fast

    async def check_availability(self) -> bool:
        """Ollamaサーバーが利用可能かを確認"""
        try:
            response = await self.client.get(f"{self._settings.ollama_base_url}/api/tags")
            self._available = response.status_code == 200
        except Exception:
            self._available = False
        return self._available

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Ollama経由でチャット補完を実行

        Args:
            messages: メッセージリスト [{"role": "system", "content": "..."}, ...]
            model: 使用するモデル（デフォルト: ollama_model）
            temperature: 温度パラメータ
            max_tokens: 最大トークン数（num_predictにマップ）

        Returns:
            アシスタントのレスポンステキスト
        """
        model = model or self._settings.ollama_model
        temperature = temperature if temperature is not None else self._settings.ollama_temperature

        options = {
            "temperature": temperature,
            "num_ctx": self._settings.ollama_num_ctx,
        }
        if max_tokens:
            options["num_predict"] = max_tokens

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        response = await self.client.post(
            f"{self._settings.ollama_base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return data["message"]["content"]

    async def chat_fast(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> str:
        """高速モデルでチャット補完を実行"""
        return await self.chat(
            messages=messages,
            model=self._settings.ollama_model_fast,
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
            model: 使用するモデル（デフォルト: ollama_model）
            temperature: 温度パラメータ

        Yields:
            生成されたトークン
        """
        model = model or self._settings.ollama_model
        temperature = temperature if temperature is not None else self._settings.ollama_temperature

        options = {
            "temperature": temperature,
            "num_ctx": self._settings.ollama_num_ctx,
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options,
        }

        async with self.client.stream(
            "POST",
            f"{self._settings.ollama_base_url}/api/chat",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> dict:
        """ヘルスチェックを実行"""
        try:
            # サーバー起動確認
            start = time.time()
            response = await self.client.get(f"{self._settings.ollama_base_url}/api/tags")

            if response.status_code != 200:
                return {
                    "healthy": False,
                    "latency_ms": 0,
                    "error": f"Server returned status {response.status_code}",
                }

            # モデル一覧を取得
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]

            # 必要なモデルがあるか確認
            model_available = any(
                self._settings.ollama_model in m or self._settings.ollama_model.split(":")[0] in m
                for m in models
            )

            latency = (time.time() - start) * 1000

            if not model_available:
                return {
                    "healthy": False,
                    "latency_ms": round(latency, 2),
                    "error": f"Model '{self._settings.ollama_model}' not found. Available: {models}",
                    "available_models": models,
                }

            return {
                "healthy": True,
                "latency_ms": round(latency, 2),
                "error": None,
                "available_models": models,
            }

        except httpx.ConnectError:
            return {
                "healthy": False,
                "latency_ms": 0,
                "error": f"Cannot connect to Ollama at {self._settings.ollama_base_url}",
            }
        except Exception as e:
            return {
                "healthy": False,
                "latency_ms": 0,
                "error": str(e),
            }

    async def pull_model(self, model: Optional[str] = None) -> dict:
        """モデルをダウンロード"""
        model = model or self._settings.ollama_model

        try:
            response = await self.client.post(
                f"{self._settings.ollama_base_url}/api/pull",
                json={"name": model, "stream": False},
                timeout=600,  # モデルダウンロードは時間がかかる
            )
            response.raise_for_status()
            return {"success": True, "model": model}
        except Exception as e:
            return {"success": False, "model": model, "error": str(e)}

    async def close(self):
        """クライアントを閉じる"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def get_status(self) -> dict:
        """拡張ステータス情報"""
        status = super().get_status()
        status["base_url"] = self._settings.ollama_base_url
        status["num_ctx"] = self._settings.ollama_num_ctx
        return status
