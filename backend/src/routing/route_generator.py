"""キャッシュベースのルート候補生成"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from src.geocoding import LocationCache, Location, get_location_cache
from src.llm.schemas import RouteFeatures, DestinationExtraction, WaypointType, ExtractedWaypoint
from .schemas import Coordinates
from .route_cache import RouteCache, get_route_cache

logger = logging.getLogger(__name__)

# 抽象的な目的地を示すキーワード
ABSTRACT_DESTINATION_KEYWORDS = [
    "温泉", "キャンプ場", "道の駅", "RVパーク", "サービスエリア",
    "海", "山", "湖", "川", "景色の良い場所", "静かな場所",
    "パーキングエリア", "車中泊スポット", "ビーチ", "森",
]


class CachedRouteGenerator:
    """
    座標キャッシュを使用したルート候補生成

    LLMで抽出した目的地情報を元に、キャッシュから
    マッチする場所を検索してルート候補を生成する。
    事前計算されたルートキャッシュがあれば、実際の道路距離・時間を使用。
    """

    ROUTE_IDS = ["A", "B", "C", "D", "E", "F", "G", "H"]

    def __init__(
        self,
        location_cache: Optional[LocationCache] = None,
        route_cache: Optional[RouteCache] = None,
    ):
        self.cache = location_cache or get_location_cache()
        self.route_cache = route_cache or get_route_cache()

    def generate_candidates(
        self,
        origin: Coordinates,
        extraction: DestinationExtraction,
        count: int = 4,
        current_time: Optional[datetime] = None,
    ) -> list[RouteFeatures]:
        """
        LLM抽出結果に基づいてルート候補を生成

        Args:
            origin: 出発地点
            extraction: LLMで抽出した目的地情報
            count: 生成する候補数
            current_time: 現在時刻

        Returns:
            ルート候補リスト
        """
        current_time = current_time or datetime.now()

        # waypointsがある場合は経由地ベースのルート生成（単一候補）
        if extraction.waypoints:
            return self._generate_waypoint_routes(
                origin=origin,
                extraction=extraction,
                current_time=current_time,
            )

        # waypointsがない場合: 検索条件で候補を生成（単一候補）
        return self._generate_destination_candidates(
            origin=origin,
            extraction=extraction,
            count=1,
            current_time=current_time,
        )

    def _generate_destination_candidates(
        self,
        origin: Coordinates,
        extraction: DestinationExtraction,
        count: int,
        current_time: datetime,
    ) -> list[RouteFeatures]:
        """従来のロジック: 目的地候補を生成"""
        # キャッシュから検索
        search_results = self.cache.search(
            place_names=extraction.place_names,
            facility_types=extraction.facility_types,
            amenities=extraction.amenities,
            atmosphere=extraction.atmosphere,
            limit=count * 2,  # 多めに取得してフィルタリング
        )

        logger.info(
            f"Search results: {len(search_results)} locations for query: "
            f"places={extraction.place_names}, "
            f"facilities={extraction.facility_types}"
        )

        # 検索結果が少ない場合は全件から補完
        if len(search_results) < count:
            all_locations = self.cache.get_all()
            existing_ids = {r.location.id for r in search_results}

            # 景観スコアでソートして追加
            sorted_locations = sorted(
                [loc for loc in all_locations if loc.id not in existing_ids],
                key=lambda x: x.scenery_score,
                reverse=True,
            )

            for loc in sorted_locations[: count - len(search_results)]:
                from src.geocoding.models import SearchResult
                search_results.append(SearchResult(
                    location=loc,
                    score=loc.scenery_score,
                    match_reasons=["景観スコアによる補完"],
                ))

        # 上位count件を選択
        selected = search_results[:count]

        # RouteFeatures に変換
        candidates = []
        for i, result in enumerate(selected):
            route_id = self.ROUTE_IDS[i] if i < len(self.ROUTE_IDS) else f"R{i}"
            candidate = self._create_route_feature(
                route_id=route_id,
                location=result.location,
                origin=origin,
                current_time=current_time,
                match_reasons=result.match_reasons,
            )
            candidates.append(candidate)

        return candidates

    def _generate_waypoint_routes(
        self,
        origin: Coordinates,
        extraction: DestinationExtraction,
        current_time: datetime,
    ) -> list[RouteFeatures]:
        """
        経由地を順番に結ぶルートを生成

        経由地が指定されている場合、各経由地をキャッシュから検索して
        1つのルート候補を生成する。最終目的地のみをRouteFeatures
        として返すが、waypointsの情報は保持される。
        """
        waypoints = sorted(extraction.waypoints, key=lambda w: w.order)
        if not waypoints:
            return []

        # 最終目的地を取得
        final_waypoint = next(
            (w for w in waypoints if w.type == WaypointType.FINAL),
            waypoints[-1]  # FINALがなければ最後のwaypointを使用
        )

        # 最終目的地をキャッシュから検索
        final_location = self._find_location_by_name(final_waypoint.name)

        if not final_location:
            # キャッシュにない場合は施設タイプとして検索
            search_results = self.cache.search(
                place_names=[final_waypoint.name],
                facility_types=[final_waypoint.name],
                limit=1,
            )
            if search_results:
                final_location = search_results[0].location

        if not final_location:
            logger.warning(f"Final destination not found: {final_waypoint.name}")
            # フォールバック: 従来のロジックで候補を生成
            return self._generate_destination_candidates(
                origin=origin,
                extraction=extraction,
                count=4,
                current_time=current_time,
            )

        # 経由地間の距離・時間・ポリラインを累積計算
        total_distance = 0.0
        total_duration = 0
        polylines: list[str] = []
        current_pos: Coordinates | Location = origin
        current_location_id: str | None = "tokyo_station"  # デフォルト出発地点

        for wp in waypoints:
            wp_location = self._find_location_by_name(wp.name)
            if wp_location:
                # 経由地までの距離・時間・ポリラインを計算
                segment_distance, segment_duration, segment_polyline = self._calculate_segment(
                    current_pos, wp_location, current_location_id
                )
                total_distance += segment_distance
                total_duration += segment_duration
                if segment_polyline:
                    polylines.append(segment_polyline)

                # 次のセグメントの起点を更新
                current_pos = wp_location
                current_location_id = wp_location.id
            else:
                # 経由地が見つからない場合は概算を追加
                total_distance += 10  # 概算10km
                total_duration += 15  # 概算15分
                current_location_id = None  # 次のキャッシュ検索はスキップ

        # 到着予定時刻
        eta = current_time + timedelta(minutes=total_duration)

        # 高速料金（距離に応じて概算）
        toll_fee = int(total_distance * 25) if total_distance > 30 else 0

        # 周辺施設
        nearby_facilities = final_location.facilities.copy()
        if final_location.ev_charging and "EV充電" not in nearby_facilities:
            nearby_facilities.append("EV充電")

        # 経由地の名前を追加情報として含める
        waypoint_names = [w.name for w in waypoints if w.type != WaypointType.FINAL]
        if waypoint_names:
            nearby_facilities.insert(0, f"経由: {', '.join(waypoint_names)}")

        # ポリラインを結合（簡易版: セグメントを連結）
        combined_polyline = self._combine_polylines(polylines) if polylines else None

        route = RouteFeatures(
            id="A",  # 経由地指定ルートは単一候補
            destination_name=final_location.name,
            eta=eta,
            distance_km=round(total_distance, 1),
            duration_minutes=total_duration,
            toll_fee=toll_fee,
            charging_available=final_location.ev_charging,
            noise_level=final_location.noise_level,
            scenery_score=final_location.scenery_score,
            nearby_facilities=nearby_facilities,
            polyline=combined_polyline,
        )

        return [route]

    def _generate_abstract_waypoint_routes(
        self,
        origin: Coordinates,
        extraction: DestinationExtraction,
        count: int,
        current_time: datetime,
    ) -> list[RouteFeatures]:
        """
        抽象的な目的地を複数の具体的候補に展開してルートを生成

        例: "温泉" → [箱根温泉, 草津温泉, 熱海温泉, 有馬温泉]

        Args:
            origin: 出発地点
            extraction: LLMで抽出した目的地情報
            count: 生成する候補数
            current_time: 現在時刻

        Returns:
            複数のルート候補リスト
        """
        waypoints = sorted(extraction.waypoints, key=lambda w: w.order)
        final_waypoint = self._get_final_waypoint(waypoints)

        if not final_waypoint:
            return []

        # 具体的な経由地（途中経由）を取得
        concrete_waypoints = [w for w in waypoints if w != final_waypoint]

        # 抽象的な最終目的地を施設種別として検索
        search_results = self.cache.search(
            place_names=[final_waypoint.name],
            facility_types=[final_waypoint.name],
            amenities=extraction.amenities,
            atmosphere=extraction.atmosphere,
            limit=count * 2,  # 多めに取得
        )

        logger.info(
            f"Abstract destination search: {final_waypoint.name} -> "
            f"{len(search_results)} results"
        )

        # 結果が少ない場合はタグ検索で補完
        if len(search_results) < count:
            # タグでの検索を試行
            all_locations = self.cache.get_all()
            existing_ids = {r.location.id for r in search_results}

            # 最終目的地名に関連するタグを持つLocationを検索
            for loc in all_locations:
                if loc.id in existing_ids:
                    continue
                # タグに最終目的地名が含まれるかチェック
                if any(final_waypoint.name in tag for tag in loc.tags):
                    from src.geocoding.models import SearchResult
                    search_results.append(SearchResult(
                        location=loc,
                        score=loc.scenery_score,
                        match_reasons=[f"タグマッチ: {final_waypoint.name}"],
                    ))
                if len(search_results) >= count * 2:
                    break

        # 上位count件を選択
        selected = search_results[:count]

        # 各候補に対してルートを生成
        candidates = []
        for i, result in enumerate(selected):
            route_id = self.ROUTE_IDS[i] if i < len(self.ROUTE_IDS) else f"R{i}"

            if concrete_waypoints:
                # 経由地あり: 経由地 + 候補地点
                route = self._create_route_with_waypoints(
                    route_id=route_id,
                    origin=origin,
                    waypoints=concrete_waypoints,
                    final_location=result.location,
                    current_time=current_time,
                    match_reasons=result.match_reasons,
                )
            else:
                # 経由地なし: 直接候補地点へ
                route = self._create_route_feature(
                    route_id=route_id,
                    location=result.location,
                    origin=origin,
                    current_time=current_time,
                    match_reasons=result.match_reasons,
                )

            candidates.append(route)

        return candidates

    def _create_route_with_waypoints(
        self,
        route_id: str,
        origin: Coordinates,
        waypoints: list[ExtractedWaypoint],
        final_location: Location,
        current_time: datetime,
        match_reasons: list[str],
    ) -> RouteFeatures:
        """
        経由地 + 最終地点でルートを構築

        Args:
            route_id: ルートID
            origin: 出発地点
            waypoints: 経由地リスト（最終目的地を除く）
            final_location: 最終目的地のLocation
            current_time: 現在時刻
            match_reasons: マッチ理由

        Returns:
            構築されたRouteFeatures
        """
        # 距離・時間の累積計算
        total_distance = 0.0
        total_duration = 0
        polylines: list[str] = []
        current_pos: Coordinates | Location = origin
        current_id: str | None = "tokyo_station"

        # 経由地を順に処理
        for wp in waypoints:
            wp_location = self._find_location_by_name(wp.name)
            if wp_location:
                dist, dur, poly = self._calculate_segment(
                    current_pos, wp_location, current_id
                )
                total_distance += dist
                total_duration += dur
                if poly:
                    polylines.append(poly)
                current_pos = wp_location
                current_id = wp_location.id
            else:
                # 経由地が見つからない場合は概算を追加
                total_distance += 10  # 概算10km
                total_duration += 15  # 概算15分
                current_id = None

        # 最終地点
        dist, dur, poly = self._calculate_segment(
            current_pos, final_location, current_id
        )
        total_distance += dist
        total_duration += dur
        if poly:
            polylines.append(poly)

        # 到着予定時刻
        eta = current_time + timedelta(minutes=total_duration)

        # 高速料金
        toll_fee = int(total_distance * 25) if total_distance > 30 else 0

        # 周辺施設
        nearby_facilities = final_location.facilities.copy()
        if final_location.ev_charging and "EV充電" not in nearby_facilities:
            nearby_facilities.append("EV充電")

        # 経由地の名前を追加情報として含める
        waypoint_names = [w.name for w in waypoints]
        if waypoint_names:
            nearby_facilities.insert(0, f"経由: {', '.join(waypoint_names)}")

        # ポリラインを結合
        combined_polyline = self._combine_polylines(polylines) if polylines else None

        return RouteFeatures(
            id=route_id,
            destination_name=final_location.name,
            eta=eta,
            distance_km=round(total_distance, 1),
            duration_minutes=total_duration,
            toll_fee=toll_fee,
            charging_available=final_location.ev_charging,
            noise_level=final_location.noise_level,
            scenery_score=final_location.scenery_score,
            nearby_facilities=nearby_facilities,
            polyline=combined_polyline,
        )

    def _generate_abstract_via_routes(
        self,
        origin: Coordinates,
        extraction: DestinationExtraction,
        abstract_waypoints: list[ExtractedWaypoint],
        count: int,
        current_time: datetime,
    ) -> list[RouteFeatures]:
        """
        抽象的な経由地を複数の具体的候補に展開してルートを生成

        最終目的地は固定で、経由地のバリエーションを生成する。
        例: "温泉経由で箱根" → [熱海温泉経由→箱根, 伊豆長岡温泉経由→箱根, ...]

        Args:
            origin: 出発地点
            extraction: LLMで抽出した目的地情報
            abstract_waypoints: 抽象的な経由地のリスト
            count: 生成する候補数
            current_time: 現在時刻

        Returns:
            複数のルート候補リスト
        """
        waypoints = sorted(extraction.waypoints, key=lambda w: w.order)
        final_waypoint = self._get_final_waypoint(waypoints)

        if not final_waypoint:
            return []

        # 最終目的地のLocationを取得
        final_location = self._find_location_by_name(final_waypoint.name)
        if not final_location:
            # キャッシュにない場合は施設タイプとして検索
            search_results = self.cache.search(
                place_names=[final_waypoint.name],
                limit=1,
            )
            if search_results:
                final_location = search_results[0].location

        if not final_location:
            logger.warning(f"Final destination not found: {final_waypoint.name}")
            return []

        # 最初の抽象経由地を展開（現時点では1つのみ対応）
        abstract_via = abstract_waypoints[0]

        # 抽象的な経由地を施設種別として検索
        search_results = self.cache.search(
            place_names=[abstract_via.name],
            facility_types=[abstract_via.name],
            amenities=extraction.amenities,
            atmosphere=extraction.atmosphere,
            limit=count * 2,
        )

        logger.info(
            f"Abstract via search: {abstract_via.name} -> "
            f"{len(search_results)} results"
        )

        # 結果が少ない場合はタグ検索で補完
        if len(search_results) < count:
            all_locations = self.cache.get_all()
            existing_ids = {r.location.id for r in search_results}

            for loc in all_locations:
                if loc.id in existing_ids:
                    continue
                if any(abstract_via.name in tag for tag in loc.tags):
                    from src.geocoding.models import SearchResult
                    search_results.append(SearchResult(
                        location=loc,
                        score=loc.scenery_score,
                        match_reasons=[f"タグマッチ: {abstract_via.name}"],
                    ))
                if len(search_results) >= count * 2:
                    break

        # 上位count件を選択
        selected = search_results[:count]

        # 具体的な経由地（抽象でないもの）を取得
        concrete_waypoints = [
            w for w in waypoints
            if w != final_waypoint and w not in abstract_waypoints
        ]

        # 各候補に対してルートを生成
        candidates = []
        for i, result in enumerate(selected):
            route_id = self.ROUTE_IDS[i] if i < len(self.ROUTE_IDS) else f"R{i}"

            # 抽象経由地を具体的な地点に置き換えた経由地リストを作成
            expanded_waypoints = []
            for wp in waypoints:
                if wp == final_waypoint:
                    continue
                if wp == abstract_via:
                    # 抽象経由地を具体的な地点に置き換え
                    expanded_waypoints.append(ExtractedWaypoint(
                        name=result.location.name,
                        type=wp.type,
                        order=wp.order,
                        purpose=wp.purpose,
                        duration_hint=wp.duration_hint,
                    ))
                else:
                    expanded_waypoints.append(wp)

            # ルートを生成
            route = self._create_route_with_waypoints(
                route_id=route_id,
                origin=origin,
                waypoints=expanded_waypoints,
                final_location=final_location,
                current_time=current_time,
                match_reasons=result.match_reasons,
            )

            candidates.append(route)

        return candidates

    def _generate_facility_based_routes(
        self,
        origin: Coordinates,
        extraction: DestinationExtraction,
        count: int,
        current_time: datetime,
    ) -> list[RouteFeatures]:
        """
        facility_typesに基づいて複数候補を生成

        LLMが具体的な地名を返しても、facility_typesが抽象的な場合は
        複数の候補を生成する。例: LLMが「箱根温泉」を返しても、
        facility_types=["温泉"]なら複数の温泉候補を出す。

        Args:
            origin: 出発地点
            extraction: LLMで抽出した目的地情報
            count: 生成する候補数
            current_time: 現在時刻

        Returns:
            複数のルート候補リスト
        """
        # facility_typesで検索
        search_results = self.cache.search(
            place_names=extraction.place_names,
            facility_types=extraction.facility_types,
            amenities=extraction.amenities,
            atmosphere=extraction.atmosphere,
            limit=count * 2,
        )

        logger.info(
            f"Facility-based search: types={extraction.facility_types} -> "
            f"{len(search_results)} results"
        )

        # 結果が少ない場合は補完
        if len(search_results) < count:
            all_locations = self.cache.get_all()
            existing_ids = {r.location.id for r in search_results}

            # facility_typesに関連するタグを持つLocationを検索
            for loc in all_locations:
                if loc.id in existing_ids:
                    continue
                for facility_type in extraction.facility_types:
                    if any(facility_type in tag for tag in loc.tags):
                        from src.geocoding.models import SearchResult
                        search_results.append(SearchResult(
                            location=loc,
                            score=loc.scenery_score,
                            match_reasons=[f"タグマッチ: {facility_type}"],
                        ))
                        break
                if len(search_results) >= count * 2:
                    break

        # 上位count件を選択
        selected = search_results[:count]

        # 各候補に対してルートを生成
        candidates = []
        for i, result in enumerate(selected):
            route_id = self.ROUTE_IDS[i] if i < len(self.ROUTE_IDS) else f"R{i}"

            candidate = self._create_route_feature(
                route_id=route_id,
                location=result.location,
                origin=origin,
                current_time=current_time,
                match_reasons=result.match_reasons,
            )
            candidates.append(candidate)

        return candidates

    def _has_abstract_facility_type(self, facility_types: list[str]) -> bool:
        """
        facility_typesに抽象的なキーワードが含まれているかチェック

        Args:
            facility_types: 施設種別リスト

        Returns:
            抽象的なキーワードが含まれている場合True
        """
        for facility_type in facility_types:
            if facility_type in ABSTRACT_DESTINATION_KEYWORDS:
                return True
            # 部分一致もチェック
            for kw in ABSTRACT_DESTINATION_KEYWORDS:
                if kw in facility_type or facility_type in kw:
                    return True
        return False

    def _combine_polylines(self, polylines: list[str]) -> str | None:
        """
        複数のポリラインを結合

        Google Polyline形式のエンコードされた文字列を
        デコード→座標結合→再エンコードして1つのポリラインにする。

        Args:
            polylines: エンコードされたポリラインのリスト

        Returns:
            結合されたポリライン
        """
        if not polylines:
            return None
        if len(polylines) == 1:
            return polylines[0]

        # 全ポリラインをデコードして座標を結合
        all_coords: list[tuple[float, float]] = []
        for polyline in polylines:
            coords = self._decode_polyline(polyline)
            if coords:
                # 重複する接続点を除去（前のセグメントの終点と次の始点が同じ場合）
                if all_coords and coords and all_coords[-1] == coords[0]:
                    coords = coords[1:]
                all_coords.extend(coords)

        if not all_coords:
            return None

        # 再エンコード
        return self._encode_polyline(all_coords)

    def _decode_polyline(self, encoded: str) -> list[tuple[float, float]]:
        """
        Google Polyline形式をデコード

        Args:
            encoded: エンコードされたポリライン文字列

        Returns:
            座標リスト [(lat, lng), ...]
        """
        coords = []
        index = 0
        lat = 0
        lng = 0

        while index < len(encoded):
            # 緯度をデコード
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            lat += (~(result >> 1) if result & 1 else result >> 1)

            # 経度をデコード
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            lng += (~(result >> 1) if result & 1 else result >> 1)

            coords.append((lat / 1e5, lng / 1e5))

        return coords

    def _encode_polyline(self, coords: list[tuple[float, float]]) -> str:
        """
        座標リストをGoogle Polyline形式にエンコード

        Args:
            coords: 座標リスト [(lat, lng), ...]

        Returns:
            エンコードされたポリライン文字列
        """
        def encode_value(value: int) -> str:
            """単一の値をエンコード"""
            value = ~(value << 1) if value < 0 else value << 1
            chunks = []
            while value >= 0x20:
                chunks.append(chr((0x20 | (value & 0x1f)) + 63))
                value >>= 5
            chunks.append(chr(value + 63))
            return ''.join(chunks)

        result = []
        prev_lat = 0
        prev_lng = 0

        for lat, lng in coords:
            lat_int = round(lat * 1e5)
            lng_int = round(lng * 1e5)

            result.append(encode_value(lat_int - prev_lat))
            result.append(encode_value(lng_int - prev_lng))

            prev_lat = lat_int
            prev_lng = lng_int

        return ''.join(result)

    def _get_final_waypoint(
        self, waypoints: list[ExtractedWaypoint]
    ) -> Optional[ExtractedWaypoint]:
        """
        waypointsから最終目的地を取得

        Args:
            waypoints: 経由地リスト

        Returns:
            最終目的地のwaypoint（なければNone）
        """
        if not waypoints:
            return None

        # FINALタイプを優先
        final = next(
            (w for w in waypoints if w.type == WaypointType.FINAL),
            None
        )
        if final:
            return final

        # FINALがなければ最後のwaypointを使用
        sorted_waypoints = sorted(waypoints, key=lambda w: w.order)
        return sorted_waypoints[-1] if sorted_waypoints else None

    def _get_abstract_waypoints(
        self, waypoints: list[ExtractedWaypoint]
    ) -> list[ExtractedWaypoint]:
        """
        waypointsから抽象的な経由地を抽出（最終目的地を除く）

        Args:
            waypoints: 経由地リスト

        Returns:
            抽象的な経由地のリスト
        """
        final_waypoint = self._get_final_waypoint(waypoints)
        abstract_waypoints = []

        for wp in waypoints:
            # 最終目的地は除外
            if final_waypoint and wp == final_waypoint:
                continue
            # 抽象的かどうか判定
            if self._is_abstract_destination(wp):
                abstract_waypoints.append(wp)

        return abstract_waypoints

    def _is_abstract_destination(self, waypoint: ExtractedWaypoint) -> bool:
        """
        目的地が抽象的（施設種別など）かどうかを判定

        具体的な地名（キャッシュに完全一致）を優先し、
        それ以外でキーワードに該当する場合に抽象的と判定する。

        Args:
            waypoint: 判定対象のwaypoint

        Returns:
            抽象的な目的地かどうか
        """
        name = waypoint.name

        # 1. キャッシュに完全一致するLocationがあれば具体的
        # （例: 「箱根温泉」「草津温泉」など固有の地名）
        location = self.cache.get_by_name(name)
        if location:
            return False

        # キャッシュの全地点で完全一致チェック
        all_locations = self.cache.get_all()
        if any(loc.name == name for loc in all_locations):
            return False

        # 2. キーワードリストに完全一致する場合は抽象的
        # （例: 「温泉」「キャンプ場」「海」など）
        if name in ABSTRACT_DESTINATION_KEYWORDS:
            return True

        # 3. 名前が短い（1-3文字）場合は抽象的とみなす
        # （例: 「海」「山」「湖」「川」など）
        if len(name) <= 3:
            return True

        # 4. キーワードが名前に含まれ、かつ名前がキーワード+1-2文字程度
        # （例: 「温泉地」「海辺」は抽象的、「箱根温泉」は具体的で2でフィルタ済み）
        for kw in ABSTRACT_DESTINATION_KEYWORDS:
            if kw in name and len(name) <= len(kw) + 2:
                return True

        # 5. 名前が部分一致しかない場合（キーワードそのもの）
        # （例: 「温泉」は「箱根温泉」に部分一致するが完全一致はない）
        has_partial_match = any(name in loc.name or loc.name in name for loc in all_locations)
        if has_partial_match:
            for kw in ABSTRACT_DESTINATION_KEYWORDS:
                if name == kw or kw == name:
                    return True

        return False

    def _find_location_by_name(self, name: str) -> Optional[Location]:
        """名前でキャッシュからLocationを検索"""
        location = self.cache.get_by_name(name)
        if location:
            return location

        # 部分一致で検索
        all_locations = self.cache.get_all()
        for loc in all_locations:
            if name in loc.name or loc.name in name:
                return loc

        return None

    def _calculate_segment(
        self,
        start: Coordinates | Location,
        end: Location,
        start_location_id: str | None = None,
    ) -> tuple[float, int, str | None]:
        """
        2点間の距離、時間、ポリラインを計算

        Args:
            start: 出発地点（Coordinatesまたは Location）
            end: 到着地点
            start_location_id: 出発地点のID（事前計算ルート検索用）

        Returns:
            (距離km, 所要時間分, ポリライン)
        """
        # 事前計算ルートキャッシュを確認
        if start_location_id:
            cached_route = self.route_cache.get(start_location_id, end.id)
            if cached_route:
                return (
                    cached_route.distance_km,
                    cached_route.duration_minutes,
                    cached_route.polyline or None,
                )

        # デフォルトオリジン（東京駅）からのルートも確認
        cached_route = self.route_cache.get_from_default_origin(end.id)
        if cached_route:
            return (
                cached_route.distance_km,
                cached_route.duration_minutes,
                cached_route.polyline or None,
            )

        # フォールバック: 直線距離 × 道路係数で概算
        if isinstance(start, Location):
            start_lat, start_lng = start.lat, start.lng
        else:
            start_lat, start_lng = start.latitude, start.longitude

        lat_diff = abs(end.lat - start_lat)
        lng_diff = abs(end.lng - start_lng)
        straight_distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111
        distance_km = round(straight_distance * 1.3, 1)  # 道路係数
        duration_minutes = max(int(distance_km / 50 * 60), 15)  # 平均50km/h

        return distance_km, duration_minutes, None

    def _create_route_feature(
        self,
        route_id: str,
        location: Location,
        origin: Coordinates,
        current_time: datetime,
        match_reasons: list[str],
    ) -> RouteFeatures:
        """RouteFeatures オブジェクトを生成"""
        # 事前計算ルートキャッシュを確認
        cached_route = self.route_cache.get_from_default_origin(location.id)
        polyline: str | None = None

        if cached_route:
            # キャッシュから実際の道路距離・時間・ポリラインを使用
            distance_km = cached_route.distance_km
            duration_minutes = cached_route.duration_minutes
            polyline = cached_route.polyline or None
            logger.debug(f"Using cached route for {location.name}: {distance_km}km, {duration_minutes}min")
        else:
            # フォールバック: 直線距離 × 道路係数で概算
            lat_diff = abs(location.lat - origin.latitude)
            lng_diff = abs(location.lng - origin.longitude)
            straight_distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111
            distance_km = round(straight_distance * 1.3, 1)  # 道路係数
            duration_minutes = max(int(distance_km / 50 * 60), 15)  # 平均50km/h
            logger.debug(f"Fallback calculation for {location.name}: {distance_km}km, {duration_minutes}min")

        # 到着予定時刻
        eta = current_time + timedelta(minutes=duration_minutes)

        # 高速料金（距離に応じて概算）
        toll_fee = int(distance_km * 25) if distance_km > 30 else 0

        # 周辺施設（キャッシュから取得）
        nearby_facilities = location.facilities.copy()
        if location.ev_charging and "EV充電" not in nearby_facilities:
            nearby_facilities.append("EV充電")

        return RouteFeatures(
            id=route_id,
            destination_name=location.name,
            eta=eta,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            toll_fee=toll_fee,
            charging_available=location.ev_charging,
            noise_level=location.noise_level,
            scenery_score=location.scenery_score,
            nearby_facilities=nearby_facilities,
            polyline=polyline,
        )


# 後方互換性のためのエイリアス
RouteGenerator = CachedRouteGenerator
