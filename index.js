require('dotenv').config();
const express = require('express');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3001;

// リクエストの詳細をログに出力するミドルウェア関数
function logRequestDetails(req, res, next) {
    const now = new Date();
    console.log(`[${now.toISOString()}] Received ${req.method} request for ${req.url} from ${req.ip}`);
    console.log('Headers:', req.headers);
    console.log('Body:', req.body);
    next(); // 次のミドルウェア/ルートハンドラーに処理を移す
}
// ミドルウェアを適用
// カスタムミドルウェアを定義
app.use((req, res, next) => {
    const start = Date.now();
    
    // リクエストログを出力
    console.log(`Received ${req.method} request for ${req.url}`);

    // レスポンスが送信された後のイベントをリッスン
    res.on('finish', () => {
        const duration = Date.now() - start;
        // レスポンスログを出力
        console.log(`Responded to ${req.method} request for ${req.url} with status ${res.statusCode} in ${duration}ms`);
    });

    next();
});
app.use(logRequestDetails); // すべてのリクエストに対してログ出力を行う

app.get('/loginCertificate', (req, res) => {
    // stateパラメータはCSRF攻撃を防ぐためにランダムな値を生成します
    const state = uuidv4();
    const scope = encodeURIComponent('openid email profile');
    const redirectUrl = `https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=${process.env.GOOGLE_CLIENT_ID}&redirect_uri=${encodeURIComponent(process.env.GOOGLE_REDIRECT_URI)}&scope=${scope}&state=${state}`;

    // リダイレクトURLをクライアントに送信する代わりに、直接リダイレクトします
    res.redirect(302, redirectUrl);
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
