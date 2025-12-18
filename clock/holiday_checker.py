import datetime, gspread, asyncio
from logs.logger import setup_logger
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

# TEST_FORCE_UNKNOWN = True
logger = setup_logger(__name__, "logs/puncher.log")
class HolidayChecker:
    def __init__(self, credentials_json: str, sheet_id: str):
        """
        credentials_json: 服務帳號 JSON 檔路徑
        sheet_id: Google Sheet ID
        """
        self.logger = logger
        self.sheet_id = sheet_id
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(credentials_json, scopes=scope)
        self.client = gspread.authorize(creds)
        try:
            self.sheet = self.client.open_by_key(sheet_id).sheet1
        except APIError as e:
            self.logger.error(f"Google Sheets API error during init: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error while opening sheet: {e}")
            raise

    # 原始方法，留著日後參考使用
    async def get_sheet_data(self):
        """取得整個 Sheet 資料"""
        if not self.sheet:
            self.logger.exception("Sheet not initialized, cannot fetch data")
            raise RuntimeError("Sheet not initialized, cannot fetch data")
        await asyncio.sleep(0)

        try:
            return self.sheet.get_all_values()  # [[日期, 狀態, 備註], ...]
        except APIError as e:
            self.logger.error(f"Google Sheets API error: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error while fetching sheet data: {e}")
            raise

    # retry 方法
    async def get_sheet_data_with_retry(self, retries=3, delay=2):
        """
        嘗試多次取得 Sheet 資料
        """

        # ===== UNKNOWN 測試用 =====
        # if TEST_FORCE_UNKNOWN:
        #     raise RuntimeError("TEST_FORCE_UNKNOWN")
        # =======================

        last_exc = None

        for attempt in range(1, retries + 1):
            try:
                return self.sheet.get_all_values()
            except APIError as e:
                last_exc = e
                self.logger.warning(
                    f"Google Sheets API error (attempt {attempt}/{retries}): {e}"
                )
            except Exception as e:
                last_exc = e
                self.logger.warning(
                    f"Unexpected error (attempt {attempt}/{retries}): {e}"
                )

            if attempt < retries:
                await asyncio.sleep(delay)

        # 全部失敗
        raise last_exc
    
    async def is_off_today(self):
        """判斷今天是否為假日或個人請假"""
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        try:
            rows = await self.get_sheet_data_with_retry()
        except Exception as e:
            # 不炸排程，回 UNKNOWN
            self.logger.error(f"Holiday check failed, status UNKNOWN: {e}")
            return None, "UNKNOWN", "Google Sheet 無法存取"
        # 注意：只有 raise exception 才會進 except
        # return None 不會觸發 UNKNOWN 流程
        
        for row in rows:
            if len(row) < 2:
                continue
            date, status = row[0], row[1]
            note = row[2] if len(row) > 2 else ""

            if date == today_str and status in ["假日", "請假"]:
                return True, status, note
            
        return False, None, None
