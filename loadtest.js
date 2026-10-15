import http from 'k6/http';
import { check, sleep } from 'k6';

// スパイクアクセスのシナリオ設定
export const options = {
    stages: [
        { duration: '5s', target: 50 },  // 5秒で一気に50並列アクセスまで引き上げる（スパイク）
        { duration: '10s', target: 50 }, // その状態を10秒キープ
        { duration: '5s', target: 0 },   // 5秒でアクセスを収束させる
    ],
};

// 実行時に環境変数でテスト対象のURLを切り替える
// 例: k6 run -e TARGET=pattern-a loadtest.js
const targetPattern = __ENV.TARGET || 'pattern-a';
// const url = `http://localhost:8000/jobs/${targetPattern}`;
const url = `http://host.docker.internal:8000/jobs/${targetPattern}`;

export default function () {
    const res = http.get(url);

    // レスポンスが200 OKだったかチェック
    check(res, {
        'is status 200': (r) => r.status === 200,
    });

    // リクエスト間に少しだけウェイトを入れる
    sleep(0.1);
}