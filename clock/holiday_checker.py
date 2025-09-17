# holiday_checker.py
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class HolidayChecker:
    def __init__(self, credentials_json: str, sheet_id: str):
        """
        credentials_json: 服務帳號 JSON 檔路徑
        sheet_id: Google Sheet ID
        """
        self.sheet_id = sheet_id
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(sheet_id).sheet1

    def get_sheet_data(self):
        """取得整個 Sheet 資料"""
        return self.sheet.get_all_values()  # [[日期, 狀態, 備註], ...]

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
