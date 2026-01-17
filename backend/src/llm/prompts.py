from .schemas import RoutingContext

ROUTE_EVALUATION_SYSTEM = """あなたは車両ルート提案AIアシスタントです。
ユーザーの要望と複数のルート候補を分析し、最適なルートを推奨してください。

## 評価基準（優先度順）
1. ユーザーの希望到着時刻との適合性
2. ユーザーの好み（静かさ、施設など）との一致度
3. バッテリー残量と充電スポットの有無
4. コストパフォーマンス（高速料金、距離）
5. 景観・環境の質

## 出力形式
必ず以下のJSON形式で回答してください。他のテキストは含めないでください。

```json
{
  "ranking": ["A", "B", "C"],
  "recommended_id": "A",
  "explanation": "推奨理由を日本語で2-3文で記載",
  "confidence": 0.85,
  "follow_up_question": null,
  "reasoning_steps": ["思考過程1", "思考過程2", "思考過程3"]
}
```

## 注意事項
- explanationは必ず日本語で記載してください
- confidenceは0.0〜1.0の範囲で、推奨の確信度を表します
- 情報が不足している場合はfollow_up_questionに質問を記載してください
- reasoning_stepsには評価の思考過程を箇条書きで記載してください
"""


def build_route_evaluation_prompt(context: RoutingContext) -> list[dict]:
    """ルート評価用のプロンプトを構築"""

    # ユーザーリクエスト情報
    user_info = f"""## ユーザーリクエスト
- 要望: {context.user_request.text}
- 希望到着時刻: {context.user_request.desired_arrival.strftime('%Y-%m-%d %H:%M') if context.user_request.desired_arrival else '指定なし'}
- 好み: {', '.join(context.user_request.preferences) if context.user_request.preferences else '特になし'}
"""

    # 車両状態情報
    vehicle_info = f"""## 車両状態
- バッテリー残量: {context.vehicle_state.battery_level}%
- 走行可能距離: {context.vehicle_state.range_km}km
- 現在のモード: {context.vehicle_state.current_mode}
- 現在位置: ({context.vehicle_state.latitude}, {context.vehicle_state.longitude})
"""

    # ルート候補情報
    routes_info = "## ルート候補\n"
    for route in context.route_candidates:
        routes_info += f"""
### ルート {route.id}: {route.destination_name}
- 到着予定時刻: {route.eta.strftime('%Y-%m-%d %H:%M')}
- 距離: {route.distance_km}km / 所要時間: {route.duration_minutes}分
- 高速料金: {route.toll_fee}円
- 充電スポット: {'あり' if route.charging_available else 'なし'}
- 騒音レベル: {route.noise_level}
- 景観スコア: {route.scenery_score}/5.0
- 周辺施設: {', '.join(route.nearby_facilities) if route.nearby_facilities else 'なし'}
"""

    # 現在時刻
    time_info = f"""## 現在時刻
{context.current_time.strftime('%Y-%m-%d %H:%M')}
"""

    user_content = f"""{user_info}
{vehicle_info}
{time_info}
{routes_info}

上記の情報を分析し、最適なルートを推奨してください。
"""

    return [
        {"role": "system", "content": ROUTE_EVALUATION_SYSTEM},
        {"role": "user", "content": user_content},
    ]


GENERAL_CHAT_SYSTEM = """あなたはM-SUITEの車両管理AIアシスタントです。
ユーザーの質問に対して、親切かつ簡潔に日本語で回答してください。

あなたの役割:
- 車両の運用モードに関するアドバイス
- 収益最適化のための提案
- ルート計画のサポート
- 一般的な質問への回答

回答は簡潔に、2-3文程度でお願いします。
"""


def build_general_chat_prompt(message: str, context: dict | None = None) -> list[dict]:
    """汎用チャット用のプロンプトを構築"""
    system_content = GENERAL_CHAT_SYSTEM

    if context:
        system_content += f"\n\n## 追加コンテキスト\n{context}"

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": message},
    ]
