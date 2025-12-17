import requests

ACCESS_TOKEN = "W5yymOA8APqYYBsZiFKZAwP6bxz2MHuAnpIAtZvSsxSL1DbzQprnvcu2fqZ/61Hq02tH9wa8d33bDz/phyQ9h9F+/KR2GcEMFGL0VqqlQDE5UtYkOn0KwuEdZkKQ21CCcuQshYVRyYbfb942IXWQ+AdB04t89/1O/w1cDnyilFU="
USER_ID = "Ua3c6d03160de3d335b23f08304a29dfa"

def send_line_message(message, user_id=USER_ID):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        resp = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=(3, 10)
        )

        if resp.status_code != 200:
            print(f"[LINE FAILED] {resp.status_code}, {resp.text}")

    except requests.exceptions.RequestException as e:
        # 吃掉所有網路相關錯誤,通知失敗不能影響核心流程
        print(f"[LINE EXCEPTION] {e}")
