from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=71c037bba8f0f521a99912258962402a5262fba75498615b811e62f748ca288e"

def analyze_image(img_url):
    # 模拟图像分析返回文本（你可以接入真实分析函数）
    return "🔍 分析完成：当前黄金走势处于震荡区间，建议观望等待突破方向确认。"

def send_dingtalk_msg(text):
    headers = {"Content-Type": "application/json"}
    payload = {"msgtype": "text", "text": {"content": text}}
    try:
        requests.post(DINGTALK_WEBHOOK, json=payload, headers=headers)
    except Exception as e:
        print("❌ 钉钉推送失败：", e)

@app.route('/auto-analysis', methods=['POST'])
def handle_webhook():
    data = request.json
    if not data or 'image_url_list' not in data:
        return jsonify({"error": "缺少 image_url_list"}), 400

    urls = data['image_url_list']
    results = []
    for url in urls:
        result = analyze_image(url)
        results.append(result)

    full_report = "\n".join(results)
    send_dingtalk_msg(full_report)
    return jsonify({"status": "ok", "message": full_report})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10010)