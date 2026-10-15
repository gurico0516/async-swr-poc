# 急激なトラフィック集中下における分散キャッシュとデータベース結果整合性のアーキテクチャ検証

本リポジトリは、求人サイトにおける突発的なスパイクアクセス（Bot等による大量検索）を想定し、DBの負荷軽減とレスポンス遅延の防止を目的としたアーキテクチャの実証実験（PoC）環境です。

## 検証する3つのアーキテクチャ
1. **Pattern A: 直接DB参照（ベースライン）**
   - キャッシュを持たず、都度MySQLへクエリを発行する。
2. **Pattern B: 標準Cache-Aside**
   - Redisにキャッシュを保持し、TTL切れ時に同期的アクセスでDBから取得・更新する。
3. **Pattern C: 非同期SWR（提案手法）**
   - Stale While Revalidate（SWR）パターンを採用。TTL切れでも即座に古いキャッシュを返却し、裏側の非同期ワーカーが排他制御（ロック）付きでDBから最新データを取得してキャッシュを更新する。

## 技術スタック
- APIサーバー: FastAPI (Python 3.11)
- 非同期ワーカー: Python
- キャッシュ: Redis 7.0
- データベース: MySQL 8.0
- 負荷テスト: k6
- インフラ: Docker Compose

## ディレクトリ構成
```text
.
├── docker-compose.yml
├── api/             # FastAPIアプリケーションとデータシード用スクリプト
├── worker/          # Redisキューを監視しDBを非同期更新するワーカー
├── mysql/           # 初期テーブル定義 (init.sql)
├── loadtest.js      # k6負荷テストシナリオ
└── README.md
```

## 環境構築と実行手順

**1. コンテナの起動**
```bash
docker compose up -d
```

**2. テスト用ダミーデータの生成（約40万件）**
```bash
docker compose exec api python seed.py
```

**3. 負荷テストの実行**
Docker経由でk6コンテナを立ち上げ、各エンドポイントにスパイクアクセス（最大50並列）を送信します。

```bash
# Pattern A (直接DB参照)
docker run --rm -i grafana/k6 run -e TARGET=pattern-a - < loadtest.js

# Pattern B (Cache-Aside)
docker run --rm -i grafana/k6 run -e TARGET=pattern-b - < loadtest.js

# Pattern C (非同期SWR)
docker run --rm -i grafana/k6 run -e TARGET=pattern-c - < loadtest.js
```

## 実証実験の結果サマリー
k6による負荷テスト（最大50並列・20秒間）の測定結果です。

| 指標 | Pattern A (直接DB) | Pattern B (Cache-Aside) | Pattern C (非同期SWR) |
| --- | --- | --- | --- |
| **総リクエスト数** | 651件 | 6,609件 | **6,918件** |
| **平均レイテンシ** | 1.09s | 13.38ms | **8.14ms** |
| **p95レイテンシ** | 1.53s | 38.39ms | **27.36ms** |
| **最大レイテンシ** | 2.26s | 1.35s (スタンピード発生) | **318.06ms** |

**考察**
Pattern BではTTL切れの瞬間にキャッシュスタンピードが発生し、最大レイテンシが1秒以上に悪化しました。一方、Pattern C（非同期SWR）ではロック制御と即時キャッシュ返却により、最大レイテンシを318msに抑え込み、突発的なアクセス集中時でも極めて安定したパフォーマンスとDBリソースの保護を両立できることが実証されました。