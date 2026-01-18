#!/usr/bin/env python3
"""
OSRM事前計算スクリプト

公開OSRMデモサーバーを使用して、主要地点間のルートを
事前計算し、JSONファイルに保存する。

使用方法:
    # 東京駅からの全ルートのみ（高速、デフォルト）
    python scripts/precompute_routes.py

    # 全地点間のルート（経由地対応、約22分）
    python scripts/precompute_routes.py --all-pairs

注意:
    - レート制限: 1リクエスト/秒
    - 東京駅のみ: 34ルート → 約40秒
    - 全地点間: 1,190ルート → 約22分
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.geocoding import get_location_cache

# OSRM公開デモサーバー
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"

# レート制限（秒）
RATE_LIMIT = 1.1  # 安全マージン

# 出力ファイル
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "route_cache.json"


def fetch_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> Optional[dict]:
    """
    OSRMからルートを取得

    Returns:
        {
            "distance_km": float,
            "duration_minutes": int,
            "polyline": str,
            "waypoints": [[lat, lng], ...]
        }
    """
    # OSRM APIは lng,lat の順序
    url = (
        f"{OSRM_BASE_URL}/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
        f"?overview=simplified&geometries=polyline"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "M-SUITE-MVP/1.0 (Hackathon Demo)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("code") != "Ok":
            return None

        route = data["routes"][0]

        # 距離をkmに変換（APIはメートル単位）
        distance_km = round(route["distance"] / 1000, 1)

        # 時間を分に変換（APIは秒単位）
        duration_minutes = round(route["duration"] / 60)

        # ポリライン（エンコード済み）
        polyline = route.get("geometry", "")

        # Waypointsを取得（ポリラインをデコードする代わりに始点終点だけ保持）
        waypoints = [
            [origin_lat, origin_lng],
            [dest_lat, dest_lng],
        ]

        return {
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "polyline": polyline,
            "waypoints": waypoints,
        }

    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"  Error: {e}")
        return None


def compute_from_single_origin(locations, origin):
    """東京駅から全地点へのルートを計算（従来方式）"""
    routes = []
    total = len(locations)
    success = 0
    failed = 0

    print(f"\n計算開始... (約{total}秒かかります)\n")

    for i, dest in enumerate(locations):
        # 同じ地点はスキップ
        if dest.id == origin.id:
            continue

        print(f"[{i+1}/{total}] {origin.name} → {dest.name}...", end=" ", flush=True)

        result = fetch_route(
            origin.lat, origin.lng,
            dest.lat, dest.lng,
        )

        if result:
            routes.append({
                "origin_id": origin.id,
                "destination_id": dest.id,
                **result,
            })
            print(f"OK ({result['distance_km']}km, {result['duration_minutes']}分)")
            success += 1
        else:
            print("FAILED")
            failed += 1

        # レート制限
        time.sleep(RATE_LIMIT)

    return routes, success, failed


def compute_all_pairs(locations):
    """全地点間のルートを計算（経由地対応）"""
    routes = []
    total_pairs = len(locations) * (len(locations) - 1)
    current = 0
    success = 0
    failed = 0

    print(f"\n全地点間計算開始... ({total_pairs}ルート、約{int(total_pairs * RATE_LIMIT / 60)}分)\n")

    for origin in locations:
        for dest in locations:
            if origin.id == dest.id:
                continue

            current += 1
            progress = f"[{current}/{total_pairs}]"
            print(f"{progress} {origin.name} → {dest.name}...", end=" ", flush=True)

            result = fetch_route(
                origin.lat, origin.lng,
                dest.lat, dest.lng,
            )

            if result:
                routes.append({
                    "origin_id": origin.id,
                    "destination_id": dest.id,
                    **result,
                })
                print(f"OK ({result['distance_km']}km, {result['duration_minutes']}分)")
                success += 1
            else:
                print("FAILED")
                failed += 1

            # レート制限
            time.sleep(RATE_LIMIT)

    return routes, success, failed


def main():
    parser = argparse.ArgumentParser(description="OSRM事前計算スクリプト")
    parser.add_argument(
        "--all-pairs",
        action="store_true",
        help="全地点間のルートを計算（経由地対応、約22分）"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="既存のキャッシュに追加（重複は上書き）"
    )
    args = parser.parse_args()

    print("=== OSRM事前計算スクリプト ===\n")

    # 座標キャッシュをロード
    location_cache = get_location_cache()
    locations = location_cache.get_all()
    print(f"地点数: {len(locations)}")

    # 既存キャッシュをロード（--append モード用）
    existing_routes = {}
    if args.append and OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            for route in data.get("routes", []):
                key = f"{route['origin_id']}:{route['destination_id']}"
                existing_routes[key] = route
        print(f"既存キャッシュ: {len(existing_routes)} ルート")

    if args.all_pairs:
        print("モード: 全地点間（経由地対応）")
        routes, success, failed = compute_all_pairs(locations)
    else:
        # 東京駅を出発地点として固定
        origin = location_cache.get_by_id("tokyo_station")
        if not origin:
            print("Error: 東京駅が見つかりません")
            return

        print(f"モード: 単一出発地点")
        print(f"出発地点: {origin.name} ({origin.lat}, {origin.lng})")
        routes, success, failed = compute_from_single_origin(locations, origin)

    # 既存ルートとマージ
    for route in routes:
        key = f"{route['origin_id']}:{route['destination_id']}"
        existing_routes[key] = route

    final_routes = list(existing_routes.values())

    # 結果を保存
    output_data = {
        "version": "1.1.0",
        "generated_at": datetime.now().isoformat(),
        "mode": "all_pairs" if args.all_pairs else "single_origin",
        "total_routes": len(final_routes),
        "routes": final_routes,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"今回: 成功 {success}, 失敗 {failed}")
    print(f"合計: {len(final_routes)} ルート")
    print(f"保存先: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
