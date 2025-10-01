import datetime, gspread
from logs.logger import setup_logger
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

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
            self.sheet = None
        except Exception as e:
            self.logger.exception(f"Unexpected error while opening sheet: {e}")
            self.sheet = None

    def get_sheet_data(self):
        """取得整個 Sheet 資料"""
        if not self.sheet:
            self.logger.error("Sheet not initialized, cannot fetch data")
            return []
    
        try:
            return self.sheet.get_all_values()  # [[日期, 狀態, 備註], ...]
        except APIError as e:
            self.logger.error(f"Google Sheets API error: {e}")
            return []  # 或者 return None，看你需要
        except Exception as e:
            self.logger.exception(f"Unexpected error while fetching sheet data: {e}")
            return []

    def is_off_today(self):
        """判斷今天是否為假日或個人請假"""
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        for row in self.get_sheet_data():
            if len(row) < 2:
                continue
            date, status = row[0], row[1]
            note = row[2] if len(row) > 2 else ""
            if date == today_str and status in ["假日", "請假"]:
                return True, status, note
        return False, None, None
