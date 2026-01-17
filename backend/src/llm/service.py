import json
import re
from typing import Optional

from .client import QwenClient
from .schemas import RoutingContext, RouteRecommendation, ChatRequest, ChatResponse
from .prompts import build_route_evaluation_prompt, build_general_chat_prompt


class LLMService:
    """LLM関連のビジネスロジック"""

    def __init__(self, client: Optional[QwenClient] = None):
        self.client = client or QwenClient()

    async def evaluate_routes(
        self,
        context: RoutingContext,
    ) -> RouteRecommendation:
        """
        ルート候補を評価して推奨を返す

        Args:
            context: ルーティングコンテキスト（ユーザー要望、車両状態、候補ルート）

        Returns:
            ルート推奨結果
        """
        messages = build_route_evaluation_prompt(context)
        response = await self.client.chat(messages)
        return self._parse_route_response(response, context)

    def _parse_route_response(
        self,
        response: str,
        context: RoutingContext,
    ) -> RouteRecommendation:
        """LLMレスポンスをパースしてRouteRecommendationに変換"""
        try:
            # JSONブロックを抽出
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSONブロックがない場合、直接パースを試みる
                json_str = response

            data = json.loads(json_str)
            return RouteRecommendation(**data)

        except (json.JSONDecodeError, ValueError) as e:
            # パース失敗時はデフォルトの推奨を返す
            route_ids = [r.id for r in context.route_candidates]
            return RouteRecommendation(
                ranking=route_ids,
                recommended_id=route_ids[0] if route_ids else "",
                explanation=f"レスポンスのパースに失敗しました。最初の候補を推奨します。エラー: {str(e)}",
                confidence=0.3,
                follow_up_question="詳細な条件を教えていただけますか？",
                reasoning_steps=["パースエラーによりデフォルト推奨"],
            )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        汎用チャット

        Args:
            request: チャットリクエスト

        Returns:
            チャットレスポンス
        """
        messages = build_general_chat_prompt(request.message, request.context)
        response = await self.client.chat_fast(messages)

        return ChatResponse(
            message=response,
            metadata={"model": "qwen-turbo"},
        )

    async def close(self):
        """サービスを閉じる"""
        await self.client.close()
