from flask import Flask, request, jsonify, redirect, render_template, after_this_request
import requests
import time

app = Flask(__name__)

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # リクエストの処理時間を計算
    duration = time.time() - request.start_time
    # ログメッセージを構築
    log_message = f"Method: {request.method}, Path: {request.path}, Status: {response.status_code}, Duration: {duration:.2f} sec"
    # ログメッセージをコンソールに出力
    print(log_message)
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/loginStart')
def login_start():
    authRequestKey = request.headers.get('authRequestKey')
    if not authRequestKey:
        return "認証キーが見つかりません", 400

    try:
        response = requests.get('http://localhost:3001/loginCertificate', 
                                headers={"authRequestKey": authRequestKey},
                                allow_redirects=False)
        print(f"{response.status_code}")
        if response.status_code == 302:
            redirect_url = response.headers.get('Location')
            return redirect(redirect_url)
        else:
            return "予期しないレスポンスが返却されました。", 500
    except Exception as e:
        print(e)
        return "外部APIへのリクエスト中にエラーが発生しました。", 500

if __name__ == '__main__':
    print(f"Debug mode is {'on' if app.debug else 'off'}")
    app.run(debug=True, port=5000)
