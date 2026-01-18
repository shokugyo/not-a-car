#!/usr/bin/env python3
"""座標キャッシュの動作テスト"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.geocoding import LocationCache, get_location_cache


def test_cache():
    print("=== 座標キャッシュテスト ===\n")

    # キャッシュをロード
    cache = get_location_cache()
    print(f"ロード完了: {cache.count} 件\n")

    # 名前で検索
    print("--- 名前検索テスト ---")
    tests = ["箱根", "河口湖", "温泉", "東京"]
    for name in tests:
        result = cache.get_by_name(name)
        if result:
            print(f"  '{name}' → {result.name} ({result.lat}, {result.lng})")
        else:
            # 部分検索
            results = cache.search_by_name(name)
            if results:
                print(f"  '{name}' (部分一致) → {[r.name for r in results[:3]]}")
            else:
                print(f"  '{name}' → 見つかりません")

    # 複合検索
    print("\n--- 複合検索テスト ---")

    # テスト1: 温泉 + 静か
    results = cache.search(
        facility_types=["温泉"],
        atmosphere=["静か"],
        limit=5,
    )
    print(f"\n  検索: facility_types=['温泉'], atmosphere=['静か']")
    for r in results:
        print(f"    - {r.location.name} (score={r.score:.1f})")
        print(f"      理由: {', '.join(r.match_reasons[:2])}")

    # テスト2: 河口湖 + キャンプ
    results = cache.search(
        place_names=["河口湖"],
        facility_types=["キャンプ場"],
        limit=5,
    )
    print(f"\n  検索: place_names=['河口湖'], facility_types=['キャンプ場']")
    for r in results:
        print(f"    - {r.location.name} (score={r.score:.1f})")

    # テスト3: EV充電 + 道の駅
    results = cache.search(
        facility_types=["道の駅"],
        amenities=["EV充電"],
        limit=5,
    )
    print(f"\n  検索: facility_types=['道の駅'], amenities=['EV充電']")
    for r in results:
        print(f"    - {r.location.name} (EV充電: {r.location.ev_charging})")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_cache()
