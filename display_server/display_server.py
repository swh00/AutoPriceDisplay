from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.before_request
def check_auth():
    if request.endpoint == "ping":
        return

    auth_header = request.headers.get('Authorization', '')
    if auth_header != '123sdaf12124':
        return jsonify({"error": "Unauthorized"}), 403
    
@app.route('/ping')
def ping():
    return jsonify({"status": "ok"})

@app.route('/display', methods=['POST'])
def display_text():
    data = request.json
    text = data.get('text', '')

    with open('display_text.txt', 'w') as f:
        f.write(text)

    return jsonify({'status': 'text received', 'text': text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

