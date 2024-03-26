# web_server.py
import base64
import os
import uuid
from flask import Flask, jsonify, render_template, redirect, request, session
import requests
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

authrequestkey = ""

@app.route('/')
def home():
    logger.info("Serving the home page")
    return render_template('index.html')

@app.route('/loginStart', methods=['GET'])
def login_start():
    logger.info("Initiating login start")

    # ランダムなUUIDを生成
    auth_request_key = str(uuid.uuid4())
    session['authRequestKey'] = auth_request_key
    # HTTPリクエストヘッダにauthRequestKeyを設定
    headers = {'authRequestKey': auth_request_key}
    
    # リクエストの詳細をログに出力
    logger.info(f"Sending HTTP GET request to http://localhost:5001/loginCertificate with headers: {headers}")
    
    # 外部APIサーバにリクエストを送信し、authRequestKeyヘッダを含める
    response = requests.get("http://127.0.0.1:5001/loginCertificate", headers=headers)
    
    session['authRequestKey'] = auth_request_key

    # レスポンスのログを出力
    logger.info(f"Received redirect response: {response.json()}")
    
    return redirect(response.json()['redirect_url'])

@app.route('/callback', methods=['GET'])
def callback():
    # セッションからauthRequestKeyを取得
    auth_request_key = session.get('authRequestKey')
    if not auth_request_key:
        logger.error("authRequestKey not found in session.")
        return "Error: authRequestKey not found.", 400

    # 外部APIサーバのloginSessionを呼び出し
    api_url = "http://localhost:5001/loginSession"
    headers = {'Content-Type': 'application/json'}
    payload = {'authRequestKey': auth_request_key}
    response = requests.put(api_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        # loginSessionからのレスポンスを処理
        encoded_session_id = response.json().get('encoded_session_id')
        if encoded_session_id:
            # BASE64デコードしてセッションIDを取得
            session_id = base64.b64decode(encoded_session_id).decode('utf-8')
            logger.info(f"Decoded session_id: {session_id}")

            # 外部APIサーバのcontractエンドポイントを呼び出し
            contract_api_url = "http://localhost:5001/contract"
            cookies = {'session_id': session_id}
            response = requests.get(contract_api_url, cookies=cookies)
    
            if response.status_code == 200:
                contract_info = response.json()
                # 取得した契約情報を表示
                # 実際にはより複雑なHTMLテンプレートを使用することが推奨されます
                return jsonify(contract_info)
            else:
                return "Failed to retrieve contract information.", response.status_code

        else:
            logger.error("Encoded session_id not found in response.")
            return "Error: Encoded session_id not found.", 400
    else:
        logger.error(f"Failed to call loginSessionAPI: {response.status_code}")
        return "Error calling loginSessionAPI.", 500
    
    
@app.errorhandler(403)
def handle_403_error(error):
    # 403エラーが発生した際のログ出力
    logger.error(f"403 Error: Access forbidden. Request path: {request.path}, IP: {request.remote_addr}")
    return jsonify(error="403 Forbidden"), 403

@app.before_request
def before_request_logging():
    # 各リクエスト前に実行されるログ出力
    logger.info(f"Request received: Method: {request.method}, Path: {request.path}, IP: {request.remote_addr}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5555)
