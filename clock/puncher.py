import time, random, json
from selenium import webdriver
from selenium.webdriver.common.by import By
from captcha.captcha_solver import CaptchaSolver
from sent_message.line_notify import send_line_message
from logs.logger import setup_logger

logger = setup_logger(__name__, "logs/puncher.log")

class Puncher:
    def __init__(self, config_path, model_path, dataset_path):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.solver = CaptchaSolver(model_path, dataset_path)

    def _setup_driver(self):
        logger.info("啟動瀏覽器並開啟打卡頁面...")
        driver = webdriver.Chrome()
        driver.get(self.config["url"])
        time.sleep(2)
        return driver

    def _get_captcha_text(self, driver):
        captcha_element = driver.find_element(By.ID, "captchasign")
        captcha_bytes = captcha_element.screenshot_as_png
        captcha_text = self.solver.solve(captcha_bytes)
        logger.info(f"辨識到驗證碼：{captcha_text}")
        return captcha_text

    def _login_and_click(self, driver, button_id, action_name):
        """通用登入流程"""
        try:
            captcha_text = self._get_captcha_text(driver)
            driver.find_element(By.ID, "txtAccount").send_keys(self.config["username"])
            driver.find_element(By.ID, "txtPassword").send_keys(self.config["password"])
            driver.find_element(By.ID, "txtVerification").send_keys(captcha_text)

            driver.find_element(By.ID, button_id).click() 
            time.sleep(3 + random.uniform(0, 2))

            # 檢查是否有錯誤訊息
            try:
                error_msg = driver.find_element(By.ID, "lblMessage").text
                if "驗證碼錯誤" in error_msg or "帳號或密碼有誤" in error_msg:
                    msg = f"{action_name}失敗 ❌ 原因：{error_msg}"
                    send_line_message(msg)
                    logger.warning(msg)
                    return
            except:
                logger.debug("未偵測到錯誤訊息，可能登入成功")

            msg = f"{action_name}完成 ✅"
            send_line_message(msg)
            logger.info(msg)

        except Exception as e:
            logger.exception(f"{action_name}時發生未預期錯誤")
            send_line_message(f"{action_name}失敗 ❌\n原因：{str(e)}")

        finally:
            driver.quit()
            logger.info("瀏覽器關閉")

    def sign_in(self):
        logger.info("開始執行上班打卡流程")
        driver = self._setup_driver()
        self._login_and_click(driver, "btnSignIn", "上班打卡")

    def sign_out(self):
        logger.info("開始執行下班打卡流程")
        driver = self._setup_driver()
        self._login_and_click(driver, "btnSignOut", "下班打卡")
