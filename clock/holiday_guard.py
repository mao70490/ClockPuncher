import asyncio
from sent_message.line_notify import send_line_message

async def run_with_holiday_check(action_name, action_func, holiday_checker):
    """執行打卡前檢查是否是假日或請假"""
    is_off, status, note = await holiday_checker.is_off_today()
    if is_off:
        msg = f"今天為【{status}】{f'（{note}）' if note else ''}，跳過 {action_name}"
        print(msg)
        send_line_message(msg)
        return
    # 如果不是休假，才執行真正的打卡
    try:
        action_func()
    except Exception as e:
        msg = f"{action_name} 發生錯誤：{e}"
        print(msg)
        send_line_message(msg)