import subprocess, json, requests, time
from bs4 import BeautifulSoup
from sent_message.line_notify import send_line_message

class NetworkManager:
    def __init__(self, config_path="config/itp_guest.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.ssid_target = self.config["wifi_name"]

    def get_current_ssid(self):
        result = subprocess.check_output(
            "netsh wlan show interfaces", shell=True, encoding="mbcs"
        )
        for line in result.splitlines():
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
        return None

    def connect_wifi(self, ssid=None):
        target = ssid or self.ssid_target
        subprocess.run(f'netsh wlan connect name="{target}"', shell=True)

    def check_captive_portal(self):
        try:
            resp = requests.get("http://clients3.google.com/generate_204", timeout=5)
            return resp.status_code != 204  # !=204 代表需要登入(合併寫法)
        except Exception as e:
            print(f"檢查網路時發生錯誤: {e}")
            return False

    def login_portal(self):
        url = self.config["url"]

        # 先 GET 抓 token 與 wlan
        resp = requests.get(url, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        token = soup.find("input", {"name": "token"})["value"]
        wlan = soup.find("input", {"name": "wlan"})["value"]

        data = {
            "username": self.config["username"],
            "password": self.config["password"],
            "token": token,
            "wlan": wlan,
        }

        post_resp = requests.post(url, data=data, verify=False)
        return post_resp.status_code

    def ensure_network(self):
        """確保已連上正確 Wi-Fi 並登入 Portal"""
        ssid = self.get_current_ssid()
        if ssid != self.ssid_target:
            print(f"目前 SSID: {ssid}, 嘗試連線 {self.ssid_target}")
            self.connect_wifi()
            time.sleep(10)  # 等待連線成功

        if self.check_captive_portal():
            print("偵測到需要登入，準備送帳號密碼...")
            status = self.login_portal()
            print("登入結果:", status)
            if status == 200:
                msg = f"{self.ssid_target} 登入成功 ✅"
                print(msg)
                send_line_message(msg) 
            else:
                msg = f"{self.ssid_target} 登入失敗 ❌ (status={status})"
                print(msg)
                send_line_message(msg)
            return status == 200
        else:
            msg = f"已連線至 {self.ssid_target}，無需登入 ✅"
            print(msg)
            send_line_message(msg)
            return True
