# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。
出力は日本語を使用してください。

## プロジェクト概要

M-SUITEは、車両オーナーが車を異なる運用モード（宿泊施設、配送、ライドシェア）に切り替えることで受動的収入を得られる車両収益化プラットフォームです。市場状況に基づいて収益を最大化するモード選択を最適化する「Yield-Drive AI」エンジンを搭載しています。

## 開発コマンド

### バックエンド (Python/FastAPI)

```bash
# 開発サーバー起動
cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# テスト実行
cd backend && pytest

# 単一テストファイル実行
cd backend && pytest tests/test_specific.py -v

# リント・フォーマット
cd backend && black src/ && isort src/
```

### フロントエンド (React/TypeScript/Vite)

```bash
# 開発サーバー起動
cd frontend && npm run dev

# ビルド
cd frontend && npm run build

# リント
cd frontend && npm run lint

# 型チェック（ビルドに含まれる）
cd frontend && tsc
```

### Docker (フルスタック)

```bash
# 全サービス起動
docker-compose up

# リビルドして起動
docker-compose up --build

# サービス停止
docker-compose down
```

## アーキテクチャ

### バックエンド構成 (`backend/src/`)

FastAPIアプリケーション。非同期SQLAlchemyを使用し、開発時はSQLite、本番はPostgreSQL。

**主要モジュール:**
- `auth/` - JWTベース認証、Ownerモデル
- `vehicles/` - 車両管理とモード切替（VehicleMode: idle, accommodation, delivery, rideshare, maintenance, charging, transit）
- `earnings/` - 収益記録とリアルタイム収益追跡
- `yield_engine/` - AI収益最適化エンジン

**Yield-Drive AIエンジン (`yield_engine/`):**
- `optimizer.py` - メインエントリポイント、遷移コスト計算と最適モード推奨
- `predictor.py` - 市場状況に基づく各モードの収益予測
- `market_analyzer.py` - 市場状況分析（需要、価格、サージ倍率）

**設計パターン:**
- 各ドメインモジュールは `models.py`（SQLAlchemy）、`schemas.py`（Pydantic）、`service.py`（ビジネスロジック）、`router.py`（APIエンドポイント）で構成
- `get_db()` 依存性注入によるDBセッション取得
- 全モデルは `database.py` の `Base` を継承
- 設定は `config.py` のPydantic BaseSettingsで管理

### フロントエンド構成 (`frontend/src/`)

React 18 + TypeScript、Vite、Tailwind CSS、状態管理にZustandを使用。

**主要構成:**
- `api/client.ts` - 認証トークン管理付きAxios APIクライアント
- `store/index.ts` - Zustandストア（auth, vehicle, earnings, yield）
- `features/` - 機能ベースのページ（dashboard, auth）
- `components/` - ドメイン別の再利用可能コンポーネント（ui/, vehicle/）
- `types/` - バックエンドスキーマに対応するTypeScriptインターフェース
- `hooks/useWebSocket.ts` - リアルタイム更新接続

**状態管理:**
- `useAuthStore` - 認証状態とログイン/ログアウト
- `useVehicleStore` - 車両一覧、選択、モード変更
- `useEarningsStore` - 収益サマリーとリアルタイム収益
- `useYieldStore` - 車両ごとのAI予測

### WebSocketプロトコル

`/ws/realtime?token=<access_token>` に接続してリアルタイム更新を受信。

メッセージタイプ:
- `ping/pong` - キープアライブ
- `refresh` - 更新された収益とAI予測をリクエスト
- `initial` - 接続時に現在の車両状態を送信
- `heartbeat` - サーバー起点のキープアライブ

### データベースモデル

**Owner** → 複数の **Vehicle** → 複数の **Earning**

Vehicleには2つのモードenum:
- `VehicleMode` - 現在の運用モード
- `InteriorMode` - 物理的な内装構成（standard, bed, cargo, passenger）

内装モード間の遷移コストがAI推奨に影響（`optimizer.py`の`INTERIOR_CHANGE_TIME`で定義）。

## APIエンドポイント

全APIルートは `/api/v1` がプレフィックス:
- `/auth/*` - 認証（register, login, me）
- `/vehicles/*` - 車両CRUDとモード変更
- `/earnings/*` - 収益クエリとシミュレーション
- `/yield/*` - AI予測と市場データ

## 環境設定

バックエンドは `.env` ファイルから読み込み:
- `DATABASE_URL` - データベース接続文字列
- `SECRET_KEY` - JWT署名キー

開発時のデフォルトDBはSQLite（`m_suite.db`）。DockerではPostgreSQLを使用。
