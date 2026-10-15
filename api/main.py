import os
import json
import redis
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# データベース接続設定
DATABASE_URL = os.getenv("DB_URL", "mysql+pymysql://user:password@db:3306/poc_db?charset=utf8mb4")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis接続設定
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "API is running"}

# パターンA：直接DB参照（ベースライン）
@app.get("/jobs/pattern-a")
def get_jobs_pattern_a(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT id, title, category, salary, description FROM jobs ORDER BY salary DESC LIMIT 100")).mappings().all()
    return {"source": "mysql", "data": result}

# パターンB：標準Cache-Aside
@app.get("/jobs/pattern-b")
def get_jobs_pattern_b(db: Session = Depends(get_db)):
    cache_key = "jobs_all"
    
    # 1. まずRedisキャッシュを確認
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return {"source": "redis_cache", "data": json.loads(cached_data)}

    # 2. キャッシュミス時はDBから取得
    result = db.execute(text("SELECT id, title, category, salary, description FROM jobs ORDER BY salary DESC LIMIT 100")).mappings().all()
    jobs_list = [dict(row) for row in result]

    # 3. Redisにキャッシュを保存 (※後の負荷テストでスタンピードを起こしやすくするためTTLは10秒と短めに設定)
    redis_client.setex(cache_key, 10, json.dumps(jobs_list))

    return {"source": "mysql", "data": jobs_list}

# パターンC：非同期SWR（提案手法）
@app.get("/jobs/pattern-c")
def get_jobs_pattern_c(db: Session = Depends(get_db)):
    cache_key = "jobs_all_swr"
    lock_key = "update_lock"
    
    # 1. キャッシュの有無を確認
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        # 2. キャッシュがあれば即座に返却（Stale許容）
        # ただし、ロックが存在しない場合のみ、裏側のワーカーに更新イベントを発火
        if not redis_client.exists(lock_key):
            # 5秒間のロックをかける（スパイク時にワーカーへの過剰なキューイングを防ぐ）
            redis_client.setex(lock_key, 5, "locked")
            redis_client.lpush("update_queue", "trigger")
            
        return {"source": "redis_swr_stale", "data": json.loads(cached_data)}

    # 3. キャッシュが全くない初回アクセス時のみ、同期的に取得してキャッシュ＆返却
    result = db.execute(text("SELECT id, title, category, salary, description FROM jobs ORDER BY salary DESC LIMIT 100")).mappings().all()
    jobs_list = [dict(row) for row in result]
    redis_client.setex(cache_key, 60, json.dumps(jobs_list))
    
    return {"source": "mysql_initial", "data": jobs_list}