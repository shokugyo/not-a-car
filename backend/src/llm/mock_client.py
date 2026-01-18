import asyncio
import json
from typing import Optional, AsyncGenerator

from .base import BaseLLMClient, LLMProvider


class MockLLMClient(BaseLLMClient):
    """テスト・フォールバック用モッククライアント"""

    def __init__(self):
        self._model = "mock-model"
        self._model_fast = "mock-model-fast"

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.MOCK

    @property
    def is_available(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def model_name_fast(self) -> str:
        return self._model_fast

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        return self._generate_mock_response(messages)

    async def chat_fast(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> str:
        return self._generate_mock_response(messages)

    async def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """ストリーミングをシミュレート"""
        response = self._generate_mock_response(messages)
        # タイプライター効果をシミュレート
        for char in response:
            yield char
            await asyncio.sleep(0.01)  # 10ms遅延

    async def health_check(self) -> dict:
        return {
            "healthy": True,
            "latency_ms": 0.1,
            "error": None,
        }

    async def close(self):
        pass

    def _generate_mock_response(self, messages: list[dict]) -> str:
        """メッセージ内容に基づいたモックレスポンスを生成"""
        last_message = messages[-1]["content"] if messages else ""
        system_message = messages[0]["content"] if messages else ""

        # 目的地抽出リクエストの場合
        if "目的地情報を抽出" in last_message or "waypoints" in system_message:
            json_response = json.dumps({
                "waypoints": [
                    {"name": "箱根温泉", "type": "final", "order": 0, "purpose": None, "duration_hint": None}
                ],
                "facility_types": ["温泉"],
                "amenities": ["EV充電"],
                "atmosphere": ["静か"],
                "activities": ["リフレッシュ"],
                "time_constraints": None,
                "distance_preference": None,
                "original_query": ""
            }, ensure_ascii=False)
            return f"```json\n{json_response}\n```"

        # ルート評価リクエストの場合
        if "route" in last_message.lower() or "ルート" in last_message:
            json_response = json.dumps({
                "ranking": ["A", "B", "C"],
                "recommended_id": "A",
                "explanation": "道の駅 富士川は静かな環境で、希望の到着時刻に余裕を持って到着できます。充電設備も完備しており、翌朝の移動にも安心です。",
                "confidence": 0.85,
                "follow_up_question": None,
                "reasoning_steps": [
                    "ユーザーは静かな場所を希望",
                    "到着時刻22:00に対してルートAは21:30着で余裕あり",
                    "充電設備があるためバッテリー残量の心配なし"
                ]
            }, ensure_ascii=False)
            return f"```json\n{json_response}\n```"

        if "宿泊" in last_message or "accommodation" in last_message.lower():
            return "宿泊モードでは、車両を宿泊施設として提供できます。静かな場所を選んで駐車し、快適な睡眠環境を提供することが重要です。"

        if "配送" in last_message or "delivery" in last_message.lower():
            return "配送モードでは、効率的なルート設計と時間管理が重要です。荷物の積載量と配送先の優先順位を考慮しましょう。"

        if "収益" in last_message or "earnings" in last_message.lower():
            return "収益最適化には、需要予測に基づいたモード切り替えが効果的です。時間帯や曜日による需要変動を考慮しましょう。"

        return "APIキーが設定されていないため、モックレスポンスを返しています。実際のAI機能を使用するには、環境変数を設定してください。"
