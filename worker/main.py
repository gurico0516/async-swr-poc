import os
import json
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis

# 接続設定
DATABASE_URL = os.getenv("DB_URL", "mysql+pymysql://user:password@db:3306/poc_db?charset=utf8mb4")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

print("Worker is listening for update events...")

while True:
    # update_queue からタスクを取得（キューにタスクが入るまで待機）
    task = redis_client.brpop("update_queue", timeout=0)
    
    if task:
        print("Received update event. Revalidating cache...")
        db = SessionLocal()
        try:
            # 実際の重いクエリを想定した処理
            result = db.execute(text("SELECT id, title, category, salary, description FROM jobs ORDER BY salary DESC LIMIT 100")).mappings().all()
            jobs_list = [dict(row) for row in result]
            
            # キャッシュを最新化（TTLは長めの60秒）
            redis_client.setex("jobs_all_swr", 60, json.dumps(jobs_list))
            print("Cache revalidated successfully.")
        except Exception as e:
            print(f"Error updating cache: {e}")
        finally:
            db.close()