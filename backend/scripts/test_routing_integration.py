#!/usr/bin/env python3
"""ルーティング統合テスト"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.geocoding import get_location_cache
from src.llm.schemas import DestinationExtraction
from src.routing.route_generator import CachedRouteGenerator
from src.routing.schemas import Coordinates, DEFAULT_ORIGIN


async def test_route_generation():
    print("=== ルート生成テスト ===\n")

    cache = get_location_cache()
    generator = CachedRouteGenerator(cache)

    # テストケース1: 温泉に行きたい
    print("--- テスト1: 温泉に行きたい ---")
    extraction1 = DestinationExtraction(
        place_names=[],
        facility_types=["温泉"],
        amenities=[],
        atmosphere=["静か", "リラックス"],
        activities=["車中泊"],
        time_constraints=None,
        distance_preference=None,
        original_query="温泉に行きたい、静かな場所で車中泊したい",
    )

    candidates1 = generator.generate_candidates(
        origin=DEFAULT_ORIGIN,
        extraction=extraction1,
        count=4,
    )

    for c in candidates1:
        print(f"  {c.id}: {c.destination_name}")
        print(f"      距離: {c.distance_km}km, 時間: {c.duration_minutes}分")
        print(f"      施設: {', '.join(c.nearby_facilities[:4])}")

    # テストケース2: 河口湖でキャンプ
    print("\n--- テスト2: 河口湖でキャンプ ---")
    extraction2 = DestinationExtraction(
        place_names=["河口湖"],
        facility_types=["キャンプ場"],
        amenities=["シャワー"],
        atmosphere=["自然", "星空"],
        activities=[],
        time_constraints=None,
        distance_preference=None,
        original_query="河口湖でキャンプしたい",
    )

    candidates2 = generator.generate_candidates(
        origin=DEFAULT_ORIGIN,
        extraction=extraction2,
        count=4,
    )

    for c in candidates2:
        print(f"  {c.id}: {c.destination_name}")
        print(f"      距離: {c.distance_km}km, EV充電: {c.charging_available}")

    # テストケース3: 箱根方面でドライブ
    print("\n--- テスト3: 箱根方面でドライブ ---")
    extraction3 = DestinationExtraction(
        place_names=["箱根"],
        facility_types=[],
        amenities=["EV充電"],
        atmosphere=["景色が良い"],
        activities=["ドライブ"],
        time_constraints=None,
        distance_preference=None,
        original_query="箱根方面で景色の良いドライブがしたい",
    )

    candidates3 = generator.generate_candidates(
        origin=DEFAULT_ORIGIN,
        extraction=extraction3,
        count=4,
    )

    for c in candidates3:
        print(f"  {c.id}: {c.destination_name}")
        print(f"      景観スコア: {c.scenery_score}, 騒音: {c.noise_level}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    asyncio.run(test_route_generation())
