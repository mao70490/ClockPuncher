import subprocess, json, requests, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class NetworkManager:
    def __init__(self, config_path="config/itp_guest.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.ssid_target = self.config["wifi_name"]

        # 初始化 Selenium WebDriver(跳過憑證錯誤)
        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=chrome_options)

    def get_current_ssid(self):
        try:
            # 先嘗試用 bytes 取得結果，避免解碼錯誤
            result_bytes = subprocess.check_output("netsh wlan show interfaces", shell=True)
            
            # 嘗試用常見編碼依序解碼
            try:
                result = result_bytes.decode("cp950")  # Big5（繁中 Windows 常見）
            except UnicodeDecodeError:
                result = result_bytes.decode("utf-8", errors="ignore")  # 新版 Windows 常見
        except subprocess.CalledProcessError:
            return None  # netsh 執行失敗

        # 解析 SSID
        for line in result.splitlines():
            if "SSID" in line and "BSSID" not in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
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

    def login_portal(self, timeout=12):

        driver = self.driver
        wait = WebDriverWait(driver, timeout)
        success = False # 預設登入失敗

        try:
            # 前往 portal 頁面
            driver.get(self.config["url"])

            # 等待帳號欄位出現
            wait.until(EC.presence_of_element_located((By.ID, "uName")))

            # 填入帳號密碼
            driver.find_element(By.ID, "uName").send_keys(self.config["username"])
            driver.find_element(By.ID, "uPwd").send_keys(self.config["password"])

            # 勾選 checkbox
            driver.find_element(By.ID, "submitCheck").click()

            # 點擊送出按鈕
            submit_btn = driver.find_element(By.ID, "subBtn")
            WebDriverWait(driver, 5).until(lambda d: submit_btn.is_enabled())
            driver.execute_script("arguments[0].click();", submit_btn)

            # 等待導向或頁面變化
            try:
                WebDriverWait(driver, timeout).until(
                    lambda d: d.current_url != self.config["url"]
                )
                return True, "登入成功並導向新頁面", driver.current_url or "unknown"
            except TimeoutException:
                page_src = driver.page_source.lower()
                if "userid or password incorrect" in page_src:
                    return False, "登入失敗（帳號或密碼錯誤）", driver.current_url or "unknown"
                elif "error" in page_src or "invalid" in page_src or "failed" in page_src:
                    return False, "登入失敗（頁面包含錯誤訊息）", driver.current_url or "unknown"
                return True, "表單已送出，但未偵測到 redirect；請檢查是否實際登入成功", driver.current_url or "unknown"

        except TimeoutException:
            return False, "等待帳號欄位超時，可能不是在 login page", getattr(driver, "current_url", "unknown")
        except Exception as e:
            return False, f"執行例外: {e}", getattr(driver, "current_url", "unknown")
        finally:
            if success:
                driver.quit()
            else:
                print("登入失敗，保留 driver 以便檢查頁面")

    def ensure_network(self):
        """確保已連上正確 Wi-Fi 並登入 Portal"""
        ssid = self.get_current_ssid()
        if ssid != self.ssid_target:
            print(f"目前 SSID: {ssid}, 嘗試連線 {self.ssid_target}")
            self.connect_wifi()
            time.sleep(8)  # 等待連線成功

        if self.check_captive_portal():
            print("偵測到需要登入，準備送帳號密碼...")
            success, msg, cur_url = self.login_portal()
            print("登入結果:", msg)
            if success:
                line_msg = f"{self.ssid_target} 登入成功 ✅"
                print(line_msg)
                time.sleep(3)  # 等待幾秒讓網路穩定
            else:
                line_msg = f"{self.ssid_target} 登入失敗 ❌ ({msg})"
                print(line_msg)
            return success, msg
        else:
            msg = f"已連線至 {self.ssid_target}，無需登入 ✅"
            print(msg)
            return True, msg
