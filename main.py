import sys, datetime, random
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from clock.puncher import Puncher
from sent_message.line_notify import send_line_message
from clock.holiday_checker import HolidayChecker
from clock.holiday_guard import run_with_holiday_check
# ----初始化---------------------
puncher = Puncher(
    config_path=r"C:\Users\user\source\repos\AutoClock\config\config.json",
    model_path=r"C:\Users\user\source\repos\AutoClock\captcha\captcha_model.h5",
    dataset_path=r"C:\Users\user\source\repos\AutoClock\captcha_dataset"
)

checker = HolidayChecker(
    credentials_json="config/credentials.json",
    sheet_id="1Djkq8akgmFrBOxnhntJS3JdT5QZFPh5rfii1xzXrBMo"
)

scheduler = BlockingScheduler()

# -----------------------------
def schedule_today_jobs():
    """每天凌晨設定當天的上下班打卡時間（週末不排）"""
    now = datetime.datetime.now()

    # 先檢查假日/請假
    off_today, status, note = checker.is_off_today()
    if off_today:
        msg = f"今天不用打卡，狀態：{status}，備註：{note}"
        print(msg)
        send_line_message(msg)
        return

    # 週末不排
    if now.weekday() >= 5:  # 5=週六, 6=週日
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
        scheduler.add_job(puncher.sign_in, 'date', run_date=signin_time)
        msg_lines.append(f"上班打卡時間：{signin_time.strftime('%H:%M:%S')}")
    else:
        msg_lines.append("上班打卡時間：已過，今天不打卡")

    # 下班隨機時間 17:46~18:10
    hour = random.choice([17, 18])
    minute = random.randint(46, 59) if hour == 17 else random.randint(0, 10)
    signout_time = now.replace(hour=hour, minute=minute,
                               second=random.randint(0, 59), microsecond=0)
    if signout_time > now:
        scheduler.add_job(puncher.sign_out, 'date', run_date=signout_time)
        msg_lines.append(f"下班打卡時間：{signout_time.strftime('%H:%M:%S')}")
    else:
        msg_lines.append("下班打卡時間：已過，今天不打卡")

    # 測試用打卡時間
    # signin_time = now + datetime.timedelta(minutes=1 + random.randint(0, 1))
    # signout_time = now + datetime.timedelta(minutes=3 + random.randint(0, 1))

    # if signin_time:
    #     scheduler.add_job(puncher.sign_in, 'date', run_date=signin_time)
    #     print(f"今天上班打卡排程：{signin_time.strftime('%H:%M:%S')}")
    # if signout_time:
    #     scheduler.add_job(puncher.sign_out, 'date', run_date=signout_time)
    #     print(f"今天下班打卡排程：{signout_time.strftime('%H:%M:%S')}")

    msg = "今天打卡排程：\n" + "\n".join(msg_lines)
    print(msg)
    send_line_message(msg)  # 把今天排程推播到 LINE

# -----------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python main.py [signin|signout|schedule]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "signin":
        # puncher.sign_in()
        run_with_holiday_check("上班打卡", puncher.sign_in, checker)
    elif command == "signout":
        # puncher.sign_out()
        run_with_holiday_check("下班打卡", puncher.sign_out, checker)
    elif command == "schedule":
        # 啟動時就先排今天的打卡
        schedule_today_jobs()

        # 每天凌晨 00:01 安排當天的上下班打卡（排除六日）
        scheduler.add_job(
            schedule_today_jobs,
            CronTrigger(hour=0, minute=1, day_of_week="mon-fri")
        )

        print("排程啟動中…")
        scheduler.start()
    else:
        print("未知命令")
