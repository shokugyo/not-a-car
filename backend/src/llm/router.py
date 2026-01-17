from fastapi import APIRouter, Depends, HTTPException

from src.auth.dependencies import get_current_owner
from src.auth.models import Owner
from .schemas import RoutingContext, RouteRecommendation, ChatRequest, ChatResponse
from .service import LLMService

router = APIRouter()


def get_llm_service() -> LLMService:
    """LLMService依存性注入"""
    return LLMService()


@router.post("/evaluate-routes", response_model=RouteRecommendation)
async def evaluate_routes(
    request: RoutingContext,
    owner: Owner = Depends(get_current_owner),
    service: LLMService = Depends(get_llm_service),
):
    """
    ルート候補を評価して推奨を返す

    - ユーザーの要望と複数のルート候補を分析
    - 最適なルートを推奨順にランキング
    - 推奨理由を日本語で説明
    """
    try:
        result = await service.evaluate_routes(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ルート評価に失敗しました: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    owner: Owner = Depends(get_current_owner),
    service: LLMService = Depends(get_llm_service),
):
    """
    AIとの自由形式チャット

    - 車両運用に関する質問
    - 収益最適化のアドバイス
    - 一般的な質問への回答
    """
    try:
        result = await service.chat(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャットに失敗しました: {str(e)}")


@router.get("/status")
async def llm_status(
    owner: Owner = Depends(get_current_owner),
    service: LLMService = Depends(get_llm_service),
):
    """LLMサービスのステータスを確認"""
    return {
        "configured": service.client.is_configured,
        "model": service.client._settings.qwen_model,
        "model_fast": service.client._settings.qwen_model_fast,
    }
