# api/seed.py
import os
import random
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DB_URL", "mysql+pymysql://user:password@db:3306/poc_db?charset=utf8mb4")
engine = create_engine(DATABASE_URL)

CATEGORIES = ["IT", "Design", "Sales", "Marketing", "HR"]
TITLES = ["エンジニア", "デザイナー", "マネージャー", "コンサルタント", "ディレクター"]
PREFIXES = ["シニア", "ジュニア", "リード", "フロントエンド", "バックエンド", "インフラ", "AI"]

BATCH_SIZE = 10000
TOTAL_BATCHES = 40  # 1万件 × 40回 = 40万件

def generate_dummy_data(batch_size):
    data = []
    for _ in range(batch_size):
        cat = random.choice(CATEGORIES)
        title = f"{random.choice(PREFIXES)}{random.choice(TITLES)}"
        salary = random.randint(400, 1500) * 10000
        desc = f"この求人は{cat}向けの{title}のポジションです。高負荷テスト用のダミーデータとして自動生成されています。"
        data.append({"title": title, "category": cat, "salary": salary, "description": desc})
    return data

def seed_data():
    print("データ挿入を開始します...")
    with engine.begin() as conn:
        # 既存データをリセット
        conn.execute(text("TRUNCATE TABLE jobs"))
        
        for i in range(TOTAL_BATCHES):
            batch = generate_dummy_data(BATCH_SIZE)
            # バルクインサートで高速化
            conn.execute(
                text("INSERT INTO jobs (title, category, salary, description) VALUES (:title, :category, :salary, :description)"),
                batch
            )
            print(f"{(i+1)*BATCH_SIZE}件 完了...")
            
    print("40万件のデータ生成が完了しました！")

if __name__ == "__main__":
    seed_data()