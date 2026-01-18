from .schemas import RoutingContext, DestinationExtraction

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


DESTINATION_EXTRACTION_SYSTEM = """あなたは車両旅行プランニングAIです。
ユーザーの自然言語クエリから、目的地に関する情報を抽出してください。

**重要**: 以下の「候補地点情報」に含まれる地点を優先的に選択してください。
これらの地点はルート計算やEV充電情報が事前に用意されており、より正確な提案が可能です。

## 抽出する情報

1. **waypoints**: 順序付きの経由地・目的地リスト
   各waypointには以下の情報を含めます:
   - name: 地名または施設タイプ（例: "箱根", "温泉", "道の駅"）
   - type: 経由地の種類
     - "required": 必須経由（「〜経由で」「〜を通って」「〜に寄って」）
     - "optional": 任意（「できれば」「時間があれば」）
     - "final": 最終目的地
   - order: 訪問順序（0から開始）
   - purpose: 立ち寄り目的（あれば）
   - duration_hint: 滞在時間のヒント（あれば）

2. **facility_types**: 施設の種類（waypointsに含まれない追加検索条件）
   - 例: "温泉", "道の駅", "キャンプ場", "RVパーク", "サービスエリア"

3. **amenities**: 求める設備・サービス
   - 例: "EV充電", "WiFi", "シャワー", "トイレ", "コンビニ"

4. **atmosphere**: 雰囲気・環境の希望
   - 例: "静か", "景色が良い", "自然豊か", "人が少ない"

5. **activities**: やりたいこと・目的
   - 例: "車中泊", "ドライブ", "リフレッシュ", "観光", "食事"

6. **time_constraints**: 時間的な制約（あれば）
   - 例: "夜までに", "2時間以内", "日帰り"

7. **distance_preference**: 距離の希望（あれば）
   - 例: "近場", "遠出", "100km以内"

## 経由地の判定ルール

### 複数地点パターン
- 「A経由でBへ」→ A(required, order:0), B(final, order:1)
- 「Aを通ってBに行きたい」→ A(required, order:0), B(final, order:1)
- 「Aに寄ってからBへ」→ A(required, order:0), B(final, order:1)
- 「できればAに寄りたい、最終的にはB」→ A(optional, order:0), B(final, order:1)
- 「AでランチしてからBで車中泊」→ A(required, order:0, purpose:"食事"), B(final, order:1, purpose:"車中泊")

### 単一目的地パターン
- 「河口湖に行きたい」→ waypoints: [河口湖(final, order:0)]
- 「温泉に行きたい」→ waypoints: [温泉(final, order:0)], facility_types: ["温泉"]

### 抽象的なパターン（具体的な地名がない場合）
- 「静かな場所で車中泊したい」→ waypoints: [], atmosphere: ["静か"], activities: ["車中泊"]

## 出力形式
必ず以下のJSON形式で回答してください。該当がない項目は空配列またはnullにしてください。

```json
{
  "waypoints": [
    {"name": "経由地名", "type": "required", "order": 0, "purpose": null, "duration_hint": null},
    {"name": "最終目的地名", "type": "final", "order": 1, "purpose": null, "duration_hint": null}
  ],
  "facility_types": ["施設種別1"],
  "amenities": ["設備1", "設備2"],
  "atmosphere": ["雰囲気1"],
  "activities": ["活動1"],
  "time_constraints": null,
  "distance_preference": null,
  "original_query": "元のクエリ"
}
```

## 注意事項
- 明示的に言及されていない情報は推測せず、空にしてください
- 具体的な地名がある場合は必ずwaypointsに含めてください
- 曖昧な表現は適切なカテゴリに分類してください
  - "ゆっくりしたい" → atmosphere: ["静か"] または activities: ["リフレッシュ"]
  - "充電できる場所" → amenities: ["EV充電"]
"""


def build_destination_extraction_prompt(
    query: str,
    location_context: str | None = None,
) -> list[dict]:
    """
    目的地抽出用のプロンプトを構築

    Args:
        query: ユーザーの自然言語クエリ
        location_context: RAGで取得した候補地点情報（オプション）

    Returns:
        LLMに送信するメッセージリスト
    """
    system_content = DESTINATION_EXTRACTION_SYSTEM

    # RAGコンテキストがある場合はシステムプロンプトに追加
    if location_context:
        system_content += f"\n\n{location_context}"

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": f"以下のクエリから目的地情報を抽出してください:\n\n「{query}」"},
    ]
