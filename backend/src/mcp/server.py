"""
MCP (Model Context Protocol) サーバー

地点知識ベースへのアクセスを提供するMCPサーバー。
FastAPIアプリケーションに統合して使用する。
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.knowledge import KnowledgeSearch, get_knowledge_search
from src.geocoding import get_location_cache

logger = logging.getLogger(__name__)


# MCPリクエスト/レスポンスモデル
class MCPToolRequest(BaseModel):
    """MCPツール呼び出しリクエスト"""
    tool: str = Field(..., description="ツール名")
    arguments: dict = Field(default_factory=dict, description="引数")


class MCPToolResponse(BaseModel):
    """MCPツール呼び出しレスポンス"""
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None


class SearchLocationsRequest(BaseModel):
    """地点検索リクエスト"""
    query: str = Field(..., description="検索クエリ（自然言語）")
    n_results: int = Field(5, ge=1, le=10, description="返す結果数")
    require_ev_charging: bool = Field(False, description="EV充電必須")
    require_overnight_parking: bool = Field(False, description="車中泊可能必須")


class GetLocationDetailRequest(BaseModel):
    """地点詳細取得リクエスト"""
    location_id: str = Field(..., description="地点ID")


class LocationMCPServer:
    """
    地点知識ベースMCPサーバー

    以下のツールを提供:
    - search_locations: セマンティック検索で関連地点を取得
    - get_location_detail: 特定地点の詳細情報を取得
    - list_available_locations: 利用可能な全地点の概要を取得
    - get_context_for_query: LLM用のコンテキスト文字列を生成
    """

    TOOLS = {
        "search_locations": {
            "description": "ユーザーのクエリに関連する地点を検索します。温泉、キャンプ場、道の駅など35地点のデータベースから、セマンティック検索で最も関連性の高い地点を返します。",
            "parameters": {
                "query": {"type": "string", "description": "検索クエリ（例: '温泉でリラックスしたい', '富士山が見える場所'）"},
                "n_results": {"type": "integer", "description": "返す結果数（1-10）", "default": 5},
                "require_ev_charging": {"type": "boolean", "description": "EV充電必須かどうか", "default": False},
                "require_overnight_parking": {"type": "boolean", "description": "車中泊可能必須かどうか", "default": False},
            },
            "required": ["query"],
        },
        "get_location_detail": {
            "description": "特定の地点の詳細情報を取得します。名物、おすすめ時期、訪問のヒントなど、より詳細な情報を提供します。",
            "parameters": {
                "location_id": {"type": "string", "description": "地点ID（例: 'hakone_onsen', 'kawaguchiko'）"},
            },
            "required": ["location_id"],
        },
        "list_available_locations": {
            "description": "利用可能な全地点の概要リストを取得します。種別（温泉、道の駅、キャンプ場など）ごとにグループ化されています。",
            "parameters": {},
            "required": [],
        },
        "get_context_for_query": {
            "description": "ユーザーのクエリに対してLLMに渡すための最適化されたコンテキスト文字列を生成します。トークン数を考慮して、最も関連性の高い情報のみを含みます。",
            "parameters": {
                "query": {"type": "string", "description": "ユーザークエリ"},
                "max_tokens": {"type": "integer", "description": "おおよその最大トークン数", "default": 1500},
            },
            "required": ["query"],
        },
    }

    def __init__(self, use_vector_search: bool = True):
        self.knowledge_search = get_knowledge_search(use_vector_search=use_vector_search)
        self.location_cache = get_location_cache()

    def get_tools_schema(self) -> dict:
        """利用可能なツールのスキーマを返す"""
        return {
            "tools": [
                {
                    "name": name,
                    "description": info["description"],
                    "input_schema": {
                        "type": "object",
                        "properties": info["parameters"],
                        "required": info["required"],
                    },
                }
                for name, info in self.TOOLS.items()
            ]
        }

    def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """ツールを実行"""
        if tool_name == "search_locations":
            return self._search_locations(arguments)
        elif tool_name == "get_location_detail":
            return self._get_location_detail(arguments)
        elif tool_name == "list_available_locations":
            return self._list_available_locations()
        elif tool_name == "get_context_for_query":
            return self._get_context_for_query(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _search_locations(self, arguments: dict) -> dict:
        """地点検索を実行"""
        query = arguments.get("query", "")
        n_results = arguments.get("n_results", 5)
        require_ev = arguments.get("require_ev_charging", False)
        require_overnight = arguments.get("require_overnight_parking", False)

        results = self.knowledge_search.search(
            query=query,
            n_results=n_results,
            require_ev_charging=require_ev,
            require_overnight_parking=require_overnight,
        )

        return {
            "locations": [
                {
                    "id": r.id,
                    "name": r.name,
                    "prefecture": r.prefecture,
                    "type": r.type,
                    "description": r.description,
                    "specialties": r.specialties,
                    "best_season": r.best_season,
                    "tips": r.tips,
                    "ev_charging": r.ev_charging,
                    "overnight_parking": r.overnight_parking,
                    "scenery_score": r.scenery_score,
                    "relevance_score": r.relevance_score,
                }
                for r in results
            ],
            "query": query,
            "total_results": len(results),
        }

    def _get_location_detail(self, arguments: dict) -> dict:
        """地点詳細を取得"""
        location_id = arguments.get("location_id", "")
        location = self.location_cache.get_by_id(location_id)

        if not location:
            return {"error": f"Location not found: {location_id}"}

        return {
            "id": location.id,
            "name": location.name,
            "prefecture": location.prefecture,
            "type": location.type.value,
            "lat": location.lat,
            "lng": location.lng,
            "description": location.description,
            "specialties": location.specialties,
            "best_season": location.best_season,
            "tips": location.tips,
            "facilities": location.facilities,
            "aliases": location.aliases,
            "tags": location.tags,
            "ev_charging": location.ev_charging,
            "overnight_parking": location.overnight_parking,
            "noise_level": location.noise_level,
            "scenery_score": location.scenery_score,
        }

    def _list_available_locations(self) -> dict:
        """利用可能な地点一覧を取得"""
        locations = self.location_cache.get_all()

        # 種別ごとにグループ化
        by_type: dict[str, list[dict]] = {}
        for loc in locations:
            type_name = loc.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append({
                "id": loc.id,
                "name": loc.name,
                "prefecture": loc.prefecture,
            })

        return {
            "total_locations": len(locations),
            "locations_by_type": by_type,
        }

    def _get_context_for_query(self, arguments: dict) -> dict:
        """LLM用コンテキストを生成"""
        query = arguments.get("query", "")
        max_tokens = arguments.get("max_tokens", 1500)

        context = self.knowledge_search.get_context_for_llm(
            query=query,
            n_results=5,
            max_tokens=max_tokens,
        )

        return {
            "context": context,
            "query": query,
        }


def create_mcp_app() -> APIRouter:
    """MCPサーバーのFastAPIルーターを作成"""
    router = APIRouter(prefix="/mcp", tags=["MCP"])
    server = LocationMCPServer()

    @router.get("/tools")
    async def get_tools():
        """利用可能なツール一覧を取得"""
        return server.get_tools_schema()

    @router.post("/execute")
    async def execute_tool(request: MCPToolRequest) -> MCPToolResponse:
        """ツールを実行"""
        try:
            result = server.execute_tool(request.tool, request.arguments)
            return MCPToolResponse(success=True, result=result)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return MCPToolResponse(success=False, error=str(e))

    @router.post("/search")
    async def search_locations(request: SearchLocationsRequest):
        """地点検索（便利なエンドポイント）"""
        result = server.execute_tool("search_locations", request.model_dump())
        return result

    @router.get("/locations/{location_id}")
    async def get_location_detail(location_id: str):
        """地点詳細取得"""
        result = server.execute_tool("get_location_detail", {"location_id": location_id})
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result

    @router.get("/locations")
    async def list_locations():
        """地点一覧取得"""
        return server.execute_tool("list_available_locations", {})

    return router
