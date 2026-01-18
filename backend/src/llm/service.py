import json
import logging
import re
from typing import Optional, AsyncGenerator

from src.config import Settings, get_settings
from src.knowledge import get_knowledge_search, KnowledgeSearch
from .base import BaseLLMClient
from .factory import LLMClientFactory
from .fallback import FallbackLLMClient
from .schemas import (
    RoutingContext,
    RouteRecommendation,
    ChatRequest,
    ChatResponse,
    DestinationExtraction,
    ExtractedWaypoint,
    WaypointType,
)
from .prompts import build_route_evaluation_prompt, build_general_chat_prompt, build_destination_extraction_prompt

logger = logging.getLogger(__name__)


class LLMService:
    """LLM関連のビジネスロジック"""

    def __init__(
        self,
        client: Optional[BaseLLMClient] = None,
        settings: Optional[Settings] = None,
        knowledge_search: Optional[KnowledgeSearch] = None,
    ):
        self._settings = settings or get_settings()
        self._client = client
        self._initialized = client is not None
        self._knowledge_search = knowledge_search

    @property
    def client(self) -> BaseLLMClient:
        """遅延初期化でクライアントを取得"""
        if not self._initialized:
            self._client = self._create_client()
            self._initialized = True
        return self._client

    @property
    def knowledge_search(self) -> KnowledgeSearch:
        """遅延初期化でKnowledgeSearchを取得"""
        if self._knowledge_search is None:
            self._knowledge_search = get_knowledge_search()
        return self._knowledge_search

    def _create_client(self) -> BaseLLMClient:
        """設定に基づいてクライアントを作成"""
        if self._settings.llm_fallback_enabled:
            # フォールバックチェーンを構築
            clients = self._build_fallback_chain()
            return FallbackLLMClient(clients)
        else:
            return LLMClientFactory.create(settings=self._settings)

    def _build_fallback_chain(self) -> list[BaseLLMClient]:
        """フォールバックチェーンを構築"""
        from .cloud_client import QwenCloudClient
        from .ollama_client import OllamaClient
        from .mock_client import MockLLMClient

        clients = []
        provider = self._settings.llm_provider

        if provider == "cloud":
            # Cloud優先
            if self._settings.qwen_api_key:
                clients.append(QwenCloudClient(self._settings))
            clients.append(OllamaClient(self._settings))
        elif provider == "local":
            # Local優先
            clients.append(OllamaClient(self._settings))
            if self._settings.qwen_api_key:
                clients.append(QwenCloudClient(self._settings))
        elif provider == "auto":
            # Auto: APIキーがあればCloud優先、なければLocal優先
            if self._settings.qwen_api_key:
                clients.append(QwenCloudClient(self._settings))
                clients.append(OllamaClient(self._settings))
            else:
                clients.append(OllamaClient(self._settings))
        else:
            # Mock
            pass

        # 常にMockを最後のフォールバックとして追加
        clients.append(MockLLMClient())

        return clients

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

    async def extract_destination(
        self,
        query: str,
        use_rag: bool = True,
        max_context_tokens: int = 800,
    ) -> DestinationExtraction:
        """
        ユーザークエリから目的地情報を抽出

        RAGを使用して、事前キャッシュされた35地点の情報を
        LLMコンテキストに含め、より適切な地点抽出を行う。

        Args:
            query: ユーザーの自然言語クエリ
            use_rag: RAGコンテキストを使用するかどうか
            max_context_tokens: RAGコンテキストの最大トークン数

        Returns:
            抽出された目的地情報
        """
        # RAGコンテキストを取得
        location_context = None
        if use_rag:
            try:
                location_context = self.knowledge_search.get_context_for_llm(
                    query=query,
                    n_results=5,
                    max_tokens=max_context_tokens,
                )
                logger.debug(f"RAG context generated: {len(location_context)} chars")
            except Exception as e:
                logger.warning(f"Failed to get RAG context: {e}")

        messages = build_destination_extraction_prompt(query, location_context)
        response = await self.client.chat_fast(messages)
        return self._parse_extraction_response(response, query)

    async def extract_destination_stream(
        self,
        query: str,
        use_rag: bool = True,
        max_context_tokens: int = 800,
    ) -> AsyncGenerator[tuple[str, Optional[DestinationExtraction]], None]:
        """
        ストリーミングでユーザークエリから目的地情報を抽出

        Args:
            query: ユーザーの自然言語クエリ
            use_rag: RAGコンテキストを使用するかどうか
            max_context_tokens: RAGコンテキストの最大トークン数

        Yields:
            (token, extraction) - トークンと最終的な抽出結果
            処理中: (token, None)
            完了時: ("", extraction)
        """
        # RAGコンテキストを取得
        location_context = None
        if use_rag:
            try:
                location_context = self.knowledge_search.get_context_for_llm(
                    query=query,
                    n_results=5,
                    max_tokens=max_context_tokens,
                )
            except Exception as e:
                logger.warning(f"Failed to get RAG context: {e}")

        messages = build_destination_extraction_prompt(query, location_context)

        # ストリーミングでLLM応答を取得
        accumulated = ""
        async for token in self.client.chat_stream(
            messages=messages,
            model=self.client.model_name_fast,
        ):
            accumulated += token
            yield (token, None)

        # 最終的なパース結果を返す
        extraction = self._parse_extraction_response(accumulated, query)
        yield ("", extraction)

    async def evaluate_routes_stream(
        self,
        context: RoutingContext,
    ) -> AsyncGenerator[tuple[str, Optional[RouteRecommendation]], None]:
        """
        ストリーミングでルート候補を評価

        Args:
            context: ルーティングコンテキスト

        Yields:
            (token, recommendation) - トークンと最終的な推奨結果
            処理中: (token, None)
            完了時: ("", recommendation)
        """
        messages = build_route_evaluation_prompt(context)

        # ストリーミングでLLM応答を取得
        accumulated = ""
        async for token in self.client.chat_stream(messages=messages):
            accumulated += token
            yield (token, None)

        # 最終的なパース結果を返す
        recommendation = self._parse_route_response(accumulated, context)
        yield ("", recommendation)

    def _parse_extraction_response(
        self,
        response: str,
        original_query: str,
    ) -> DestinationExtraction:
        """LLMレスポンスをパースしてDestinationExtractionに変換"""
        try:
            # JSONブロックを抽出
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response

            data = json.loads(json_str)
            data["original_query"] = original_query

            # waypoints配列をExtractedWaypointオブジェクトに変換
            if "waypoints" in data and data["waypoints"]:
                waypoints = []
                for wp_data in data["waypoints"]:
                    try:
                        # typeをWaypointType enumに変換
                        wp_type = WaypointType(wp_data.get("type", "final"))
                        waypoint = ExtractedWaypoint(
                            name=wp_data.get("name", ""),
                            type=wp_type,
                            order=wp_data.get("order", 0),
                            purpose=wp_data.get("purpose"),
                            duration_hint=wp_data.get("duration_hint"),
                        )
                        waypoints.append(waypoint)
                    except (ValueError, KeyError):
                        # 個別のwaypointパース失敗時はスキップ
                        continue
                data["waypoints"] = waypoints

            return DestinationExtraction(**data)

        except (json.JSONDecodeError, ValueError):
            # パース失敗時はデフォルトを返す
            return DestinationExtraction(
                waypoints=[],
                facility_types=[],
                amenities=[],
                atmosphere=[],
                activities=[],
                time_constraints=None,
                distance_preference=None,
                original_query=original_query,
            )

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
            metadata={
                "provider": self.client.provider.value,
                "model": self.client.model_name_fast,
            },
        )

    async def health_check(self) -> dict:
        """サービスのヘルスチェック"""
        return await self.client.health_check()

    def get_status(self) -> dict:
        """サービスのステータス情報"""
        return self.client.get_status()

    async def close(self):
        """サービスを閉じる"""
        if self._initialized and self._client:
            await self._client.close()
