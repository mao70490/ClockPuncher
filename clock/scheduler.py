import datetime, random, asyncio
from datetime import timedelta # 測試用
from apscheduler.schedulers.blocking import BlockingScheduler
from clock.holiday_guard import run_with_holiday_check
from sent_message.line_notify import send_line_message
from clock.puncher import Puncher
from clock.holiday_checker import HolidayChecker
from check_net_itpg.network import NetworkManager

async def schedule_today_jobs(
        puncher: Puncher, 
        checker: HolidayChecker, 
        scheduler: BlockingScheduler, 
        network:NetworkManager = None
    ):
    """每天排當天的上下班打卡時間（週末或假日不排）"""
    now = datetime.datetime.now()

    # === 先檢查網路，確保能抓 holiday sheet ===
    if network:
        success, net_msg = network.ensure_network()
        print(f"建立排程前網路檢查: {net_msg}")
        if not success:
            send_line_message("⚠️ 網路異常，無法建立今天的打卡排程")
            return

    # 檢查假日/請假
    off_today, status, note = await checker.is_off_today()
    if off_today:
        msg = f"今天不用打卡，狀態：{status}，備註：{note}"
        print(msg)
        send_line_message(msg)
        return

    # 週末不排
    if now.weekday() >= 5:
        msg = "今天是週末，不排打卡"
        print(msg)
        send_line_message(msg)
        return

    msg_lines = []

    # 上班隨機時間 08:30~08:45
    signin_time = now.replace(
        hour=8,
        minute=random.randint(30, 45),
        second=random.randint(0, 59),
        microsecond=0
    )
    if signin_time > now:
        scheduler.add_job(
            lambda: asyncio.run(run_with_holiday_check("上班打卡", puncher.sign_in, checker, network)),
            'date', run_date=signin_time
        )
        msg_lines.append(f"簽到時間：{signin_time.strftime('%H:%M:%S')}")
    else:
        msg_lines.append("簽到時間：已過，今天不打卡")

    # 下班隨機時間 17:46~17:55
    signout_time = now.replace(
        hour=17,
        minute=random.randint(46, 55),
        second=random.randint(0, 59),
        microsecond=0
    )
    if signout_time > now:
        scheduler.add_job(
            lambda: asyncio.run(run_with_holiday_check("下班打卡", puncher.sign_out, checker, network)),
            'date', run_date=signout_time
        )
        msg_lines.append(f"簽退時間：{signout_time.strftime('%H:%M:%S')}")
    else:
        msg_lines.append("簽退時間：已過，今天不打卡")

    # -------------------- 測試用排程 ---------------------

    # 測試簽到時間：現在 + 1 分鐘
    # signin_time = now + timedelta(minutes=1)
    # scheduler.add_job(
    #     lambda: asyncio.run(run_with_holiday_check("上班打卡", puncher.sign_in, checker)),
    #     'date', run_date=signin_time
    # )
    # msg_lines.append(f"簽到時間：{signin_time.strftime('%H:%M:%S')}")

    # 測試簽退時間：現在 + 3 分鐘
    # signout_time = now + timedelta(minutes=3)
    # scheduler.add_job(
    #     lambda: asyncio.run(run_with_holiday_check("下班打卡", puncher.sign_out, checker)),
    #     'date', run_date=signout_time
    # )
    # msg_lines.append(f"簽退時間：{signout_time.strftime('%H:%M:%S')}")

    # -------------------------------------------------

    # 印訊息並推播 LINE
    msg = "======今天打卡排程======\n" + "\n".join(msg_lines)
    print(msg)
    send_line_message(msg)
