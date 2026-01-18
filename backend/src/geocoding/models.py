"""座標キャッシュのデータモデル"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LocationType(str, Enum):
    """場所の種別"""
    CITY = "city"                    # 都市
    TOWN = "town"                    # 町
    STATION = "station"              # 駅
    ONSEN = "onsen"                  # 温泉
    MICHINOEKI = "michinoeki"        # 道の駅
    CAMP = "camp"                    # キャンプ場
    RV_PARK = "rv_park"              # RVパーク
    SA_PA = "sa_pa"                  # サービスエリア・パーキングエリア
    SCENIC = "scenic"                # 景勝地
    SHRINE_TEMPLE = "shrine_temple"  # 神社仏閣
    PARK = "park"                    # 公園
    LAKE = "lake"                    # 湖
    MOUNTAIN = "mountain"            # 山
    BEACH = "beach"                  # 海岸・ビーチ
    OTHER = "other"                  # その他


class Location(BaseModel):
    """場所の座標情報"""
    id: str = Field(..., description="一意のID")
    name: str = Field(..., description="場所の名前")
    lat: float = Field(..., description="緯度")
    lng: float = Field(..., description="経度")
    type: LocationType = Field(..., description="場所の種別")
    prefecture: str = Field(..., description="都道府県")

    # 検索用タグ
    aliases: list[str] = Field(default_factory=list, description="別名・エイリアス")
    tags: list[str] = Field(default_factory=list, description="検索用タグ")
    facilities: list[str] = Field(default_factory=list, description="施設・設備")

    # 追加情報（RAG用）
    description: Optional[str] = Field(None, description="詳細な説明")
    address: Optional[str] = Field(None, description="住所")
    specialties: list[str] = Field(default_factory=list, description="名物・特産品")
    best_season: Optional[str] = Field(None, description="おすすめの季節")
    tips: Optional[str] = Field(None, description="訪問時のヒント・注意点")

    # 車中泊・EV関連
    ev_charging: bool = Field(False, description="EV充電設備あり")
    overnight_parking: bool = Field(False, description="車中泊可能")
    noise_level: str = Field("medium", description="騒音レベル (low/medium/high)")
    scenery_score: float = Field(3.0, ge=1.0, le=5.0, description="景観スコア")


class SearchResult(BaseModel):
    """検索結果"""
    location: Location
    score: float = Field(..., description="マッチスコア")
    match_reasons: list[str] = Field(default_factory=list, description="マッチ理由")
