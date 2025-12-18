import asyncio
from check_net_itpg.network import NetworkManager   
from sent_message.line_notify import send_line_message

async def run_with_holiday_check(action_name, action_func, holiday_checker, network:NetworkManager = None):
    """執行打卡前檢查是否是假日或請假"""
    try:
        # -------- 先檢查網路 --------
        if network is not None:
            success, msg = network.ensure_network()
            print(f"執行打卡前網路檢查結果: {msg}")
            if not success:
                fail_msg = f"{action_name} 失敗：無法連上 Wi-Fi"
                print(fail_msg)
                send_line_message(fail_msg)
                return

        # -------- 再檢查是否是假日 --------
        is_off, status, note = await holiday_checker.is_off_today()

        # UNKNOWN → 不打卡
        if is_off is None:
            msg = f"{action_name}：假日狀態不明（{status}），為避免誤打卡，已跳過"
            print(msg)
            send_line_message(msg)
            return

        if is_off:
            msg = f"今天為【{status}】{f'（{note}）' if note else ''}，跳過 {action_name}"
            print(msg)
            send_line_message(msg)
            return

        # -------- 真的執行打卡 --------
        action_func()

    except Exception as e:
        msg = f"{action_name} 發生錯誤：{e}"
        print(msg)
        send_line_message(msg)