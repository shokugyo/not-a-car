import json
import httpx
from typing import Optional

from src.config import Settings, get_settings


class QwenClient:
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
    def is_configured(self) -> bool:
        """APIキーが設定されているかどうか"""
        return bool(self._settings.qwen_api_key)

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

        Note:
            APIキーが未設定の場合はモックレスポンスを返す
        """
        if not self.is_configured:
            return self._mock_response(messages)

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

    def _mock_response(self, messages: list[dict]) -> str:
        """APIキー未設定時のモックレスポンス"""
        last_message = messages[-1]["content"] if messages else ""

        if "route" in last_message.lower() or "ルート" in last_message:
            return json.dumps({
                "ranking": ["A", "B", "C"],
                "recommended_id": "A",
                "explanation": "【モックレスポンス】道の駅 富士川は静かな環境で、希望の到着時刻に余裕を持って到着できます。充電設備も完備しており、翌朝の移動にも安心です。",
                "confidence": 0.85,
                "follow_up_question": None,
                "reasoning_steps": [
                    "ユーザーは静かな場所を希望",
                    "到着時刻22:00に対してルートAは21:30着で余裕あり",
                    "充電設備があるためバッテリー残量の心配なし"
                ]
            }, ensure_ascii=False)

        return "【モックレスポンス】APIキーが設定されていないため、モックレスポンスを返しています。"

    async def close(self):
        """クライアントを閉じる"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
