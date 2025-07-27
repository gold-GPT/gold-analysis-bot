# gold_screenshot_bot.py
import time
import requests
import base64
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 图表网址（TradingView 公共图表链接）
URL = "https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD"
# 图表截图保存路径
SAVE_DIR = r"D:\黄金图表"
# 图表截图周期和文件名设置
TIMEFRAMES = [
    ("1", "1min.png"),
    ("5", "5min.png"),
    ("30", "30min.png"),
    ("60", "1h.png"),
    ("120", "2h.png")
]

# ✅ Render 部署后的分析服务地址
API_ENDPOINT = "https://gold-analysis-bot.onrender.com/auto-analysis"

# ✅ 你的 imgbb 图床 API key
IMGBB_API_KEY = "4e65e446dba7abd6c81182ba67de50d0"

# ✅ 你的钉钉机器人 webhook 地址
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=71c037bba8f0f521a99912258962402a5262fba75498615b811e62f748ca288e"

def upload_to_imgbb(image_path):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read())
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": img_b64}
    )
    try:
        return response.json()["data"]["url"]
    except Exception as e:
        print("图像上传失败:", e)
        return None

def send_to_dingtalk(msg):
    headers = {"Content-Type": "application/json"}
    payload = {
        "msgtype": "text",
        "text": {"content": msg}
    }
    requests.post(DINGTALK_WEBHOOK, headers=headers, json=payload)

def capture_charts():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    time.sleep(15)  # 等待初次加载完成

    uploaded_urls = []
    for tf, filename in TIMEFRAMES:
        driver.get(f"{URL}&interval={tf}")
        time.sleep(10)
        filepath = os.path.join(SAVE_DIR, filename)
        driver.save_screenshot(filepath)
        url = upload_to_imgbb(filepath)
        if url:
            uploaded_urls.append(url)
        else:
            send_to_dingtalk(f"❌ 上传截图失败：{filename}")
    driver.quit()
    return uploaded_urls

def verify_imgbb_ready(url):
    for attempt in range(5):
        try:
            resp = requests.get(url)
            if resp.status_code == 200 and len(resp.content) > 80000:
                return True
        except:
            pass
        time.sleep(2)
    return False

def trigger_analysis(image_urls):
    # 确保图像高清就绪
    for url in image_urls:
        if not verify_imgbb_ready(url):
            return f"❌ 图像加载失败：{url}"

    payload = {"image_url_list": image_urls}
    try:
        response = requests.post(API_ENDPOINT, json=payload)
        print("返回状态码：", response.status_code)
        print("返回内容：", response.text)
        if response.status_code != 200:
            return f"❌ 分析服务异常: {response.status_code}"
        data = response.json()
        return data.get("message", "❌ 无有效返回")
    except Exception as e:
        return f"❌ 触发分析失败: {str(e)}"

if __name__ == "__main__":
    try:
        urls = capture_charts()
        if len(urls) != 5:
            send_to_dingtalk("❌ 截图上传失败，图像数量不足")
        else:
            analysis = trigger_analysis(urls)
            send_to_dingtalk("📊 黄金图表分析完成：\n" + analysis)
    except Exception as e:
        send_to_dingtalk(f"❌ 自动分析执行失败：{str(e)}")
