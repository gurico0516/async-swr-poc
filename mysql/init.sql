SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS poc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE poc_db;

CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    salary INT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO jobs (title, category, salary, description) VALUES
('シニアバックエンドエンジニア', 'IT', 8000000, 'Python/FastAPIを利用したマイクロサービス開発'),
('フロントエンドエンジニア', 'IT', 6000000, 'Vue.jsを用いたSPAの構築とパフォーマンスチューニング'),
('SRE / インフラエンジニア', 'IT', 7500000, 'AWS環境のコンテナオーケストレーションと運用自動化'),
('UI/UXデザイナー', 'Design', 5500000, 'Figmaによるデザインシステム構築'),
('データサイエンティスト', 'IT', 7000000, '検索アルゴリズムの最適化とログ解析');