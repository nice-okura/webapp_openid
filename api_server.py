# api_server.py
import base64
import uuid
from flask import Flask, redirect, request, session, url_for, jsonify
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os
import logging

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:5555/callback'

authorization_base_url = 'https://accounts.google.com/o/oauth2/auth'
token_url = 'https://accounts.google.com/o/oauth2/token'

# セッションIDとauthRequestKeyのペアを保存する簡易的なストレージ
auth_request_key_store = {}

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/loginCertificate", methods=["GET"])
def login_certificate():
    logger.info("Received login certificate request")
    auth_request_key = request.headers.get('authRequestKey')
    if not auth_request_key:
        return jsonify({"error": "authRequestKey is required"}), 400
    
    # セッションIDを生成し、ストレージに保存
    session_id = str(uuid.uuid4())
    auth_request_key_store[auth_request_key] = session_id

    google = OAuth2Session(client_id, redirect_uri=redirect_uri,
                           scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
                                  "https://www.googleapis.com/auth/userinfo.profile"])
    authorization_url, state = google.authorization_url(authorization_base_url,
                                                        access_type="offline", prompt="select_account")
    session['oauth_state'] = state

    # Flaskのセッション機構を使用してセッションIDをセット
    session['session_id'] = session_id
    
    logger.info(f"Redirecting to Google authorization url: {authorization_url}")
    return jsonify({"redirect_url": authorization_url})

@app.route("/loginSession", methods=["PUT"])
def login_session_api():
    data = request.json
    auth_request_key = data.get('authRequestKey')
    if not auth_request_key or auth_request_key not in auth_request_key_store:
        return jsonify({"error": "Invalid authRequestKey"}), 400
    
    session_id = auth_request_key_store[auth_request_key]
    encoded_session_id = base64.b64encode(session_id.encode()).decode()
    
    return jsonify({"encoded_session_id": encoded_session_id})

@app.route("/contract", methods=["GET"])
def contract():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    
    # セッションIDとauthRequestKeyのペアを確認
    for key, value in auth_request_key_store.items():
        if value == session_id:
            # ダミーの契約情報を返却
            return jsonify({"contract_info": "This is dummy contract information."})
    
    return jsonify({"error": "Invalid session_id"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5001)
